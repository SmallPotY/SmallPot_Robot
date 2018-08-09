import pymssql
import datetime
import json



class WMS:

    def __init__(self,group):

        with open("config.json","r",encoding="utf-8") as f:
            n = json.load(f)
            self.agrs = n[group]

        self.db = pymssql.connect(server=self.agrs["server"], port=self.agrs["port"], user=self.agrs["user"], password=self.agrs["password"],
                                  database=self.agrs["database"], charset="UTF-8")

    def query_rk(self, brand):

        today = datetime.date.today()

        btime = str(today - datetime.timedelta(days=25))
        etime = str(today + datetime.timedelta(days=1))
        brand_name = brand
        brand = '%' + brand + '%'

        cursor = self.db.cursor()

        sql = """SELECT RH.USER_DEF3,RD.RECEIPT_ID,RH.TOTAL_QTY,RH.TOTAL_LINES,RH.CREATE_DATE_TIME,RH.COMPANY,
        SUM(ISNULL(RC.CONVERTED_QTY,0)) CONVERTED_QTY,
        SUM(CASE WHEN RC.INVENTORY_STS='normal' THEN ISNULL(RC.QUANTITY,0) ELSE 0 END) GOOD_QTY,
        SUM(CASE WHEN RC.INVENTORY_STS!='normal' THEN ISNULL(RC.QUANTITY,0) ELSE 0 END) BAD_QTY
        FROM RECEIPT_HEADER RH WITH(NOLOCK) LEFT JOIN
        RECEIPT_DETAIL RD WITH(NOLOCK) ON RH.RECEIPT_ID=RD.RECEIPT_ID 
        LEFT JOIN  RECEIPT_CONTAINER RC WITH(NOLOCK) ON RD.INTERNAL_RECEIPT_LINE_NUM=RC.INTERNAL_RECEIPT_LINE_NUM
        WHERE 1 = 1
        AND RD.RECEIPT_ID LIKE '%s' 
        AND  RH.CREATE_DATE_TIME>= '%s'
        AND RH.CREATE_DATE_TIME<= '%s'
        GROUP BY RH.USER_DEF3,RD.RECEIPT_ID,RH.TOTAL_QTY,RH.TOTAL_LINES,RH.CREATE_DATE_TIME,RH.COMPANY
        """ % (brand, btime, etime)
        cursor.execute(sql)
        row = cursor.fetchone()
        return_text = ""
        while row:
            if row[6] == 0 and row[2] - row[7] - row[8] == 0:
                pass
            else:
                return_text = return_text + '\n-------------------\n'
                return_text = return_text + str(row[1]) + "\n"
                return_text = return_text + "总数:" + str(row[2]) + "\n"
                return_text = return_text + "已收:" + str(row[7] + row[8]) + ",未收" + str(
                    row[2] - (row[7] + row[8])) + "\n"
                return_text = return_text + "已上" + str(row[7] + row[8] - row[6]) + ",未上:" + str(row[6])

            row = cursor.fetchone()

        # 也可以使用for循环来迭代查询结果
        # for row in cursor:
        # print("ID=%d, Name=%s" % (row[0], row[1]))
        # 关闭连接
        self.db.close()

        if return_text:
            return return_text
        else:
            return "品牌[{}]查无信息".format(brand_name)



    def query_ck(self,btime,etime):

        # pc = {
        #     '4点': ['3:00', '5:00'],
        #     '11点': ['10:30', '13:00'],
        #     '15点': ['14:00', '16:30'],
        #     '19点': ['18:00', '20:00'],
        #     '23点': ['22:00', '23:59']
        # }


        # sj = pc.get(batch)

        # if not sj:
        #     return '批次不存在，目前批次有[4点,11点,15点,19点,23点]'



        # bt = str(datetime.date.today()) + " " + str(sj[0])

        # et = str(datetime.date.today()) + " " + str(sj[1])
        # print(bt,et)

        brand = tuple(self.agrs['brand'])


        sql = """
        SELECT SH.COMPANY,SH.SHIP_TO,SHIP_TO_POSTAL_CODE,SH.SHIPMENT_ID,SH.SHIP_TO_EMAIL_ADDRESS,sh.user_def1
        ,SH.INTERNAL_WAVE_NUM,SH.SHIPMENT_TYPE,SH.USER_DEF5,SH.CREATE_DATE_TIME,ISNULL(C.CONC_QTY,0) CONC_QTY, ISNULL(SUM(TD.TOTAL_QTY),0) TOTAL_QTY,ISNULL(SUM(TD.TOTAL_QTY),0)-ISNULL(SUM(TD.FROM_QTY),0) FROM_QTY
        ,ISNULL(B.PACK_QTY,0) PACK_QTY
        FROM SHIPMENT_HEADER SH WITH(NOLOCK) INNER JOIN SHIPMENT_DETAIL SD WITH(NOLOCK)
        ON SH.SHIPMENT_ID=SD.SHIPMENT_ID  LEFT JOIN TASK_DETAIL TD WITH(NOLOCK) ON
        SD.SHIPMENT_ID=TD.REFERENCE_ID AND SD.INTERNAL_SHIPMENT_LINE_NUM=TD.REFERENCE_LINE_NUM
        LEFT JOIN 
        (
        SELECT SHIPMENT_ID,SUM(QUANTITY) PACK_QTY FROM SHIPPING_CONTAINER WITH(NOLOCK) WHERE 1=1 
        AND PARENT>0 AND STATUS>=800 
        GROUP BY SHIPMENT_ID) B  ON SH.SHIPMENT_ID=B.SHIPMENT_ID
        LEFT JOIN 
        (
        SELECT SHIPMENT_ID,COUNT(1) CONC_QTY FROM SHIPPING_CONTAINER WITH(NOLOCK) WHERE 1=1 
        AND PARENT=0 AND STATUS>=800 
        GROUP BY SHIPMENT_ID
        ) C   ON SH.SHIPMENT_ID=C.SHIPMENT_ID
        WHERE 1=1 
        and SH.CREATE_DATE_TIME>='%s'
        AND SH.CREATE_DATE_TIME<='%s'
        AND SHIP_TO_POSTAL_CODE NOT IN %s
        GROUP BY SH.COMPANY,SH.SHIP_TO,SHIP_TO_POSTAL_CODE,SH.SHIPMENT_ID,SH.SHIP_TO_EMAIL_ADDRESS,sh.user_def1
        ,SH.INTERNAL_WAVE_NUM,SH.SHIPMENT_TYPE,SH.USER_DEF5,SH.CREATE_DATE_TIME,B.PACK_QTY,C.CONC_QTY
        HAVING SH.SHIPMENT_TYPE ='B2BSO'
        """ % (btime,etime,str(brand))

  
        cursor = self.db.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()

        zs = 0
        yj = 0
        yb = 0
        # return_text = "品牌|类型|总数|未拣|未包\n"
        while row:
            # return_text = return_text +  row[0] + ',' + row[1] + ',' + str(row[2]) + ',' + str(row[2] - row[3]) + ',' + str(int(row[2] - row[4])) + '\n'
            zs += int(row[11])
            yj += int(row[12])
            yb += int(row[13])
            row = cursor.fetchone()


        return_text = '订单数：' + str(zs) + ",已拣：" + str(yj) + ",已包：" + str(yb) + '\n' + '{} 至 {}'.format(btime[5:],etime[5:])
        return return_text



    def yield_table(self,btime,etime):



        user = tuple(self.agrs['username'])


        cursor = self.db.cursor()

        sql = """
        SELECT NAME,SUM(RECE_QTY) RECE_QTY,SUM(PUT_QTY) PUT_QTY,SUM(PICK_QTY) PICK_QTY,SUM(PACK_QTY) PACK_QTY,SUM(COUNTED_QTY) COUNTED_QTY,SUM(M_QTY) M_QTY FROM 
        (
        SELECT TH.USER_STAMP+'('+U.DESCRIPTION+')' NAME,SUM(QUANTITY) RECE_QTY,0 PUT_QTY,0 PICK_QTY,0 PACK_QTY,0 COUNTED_QTY,0 M_QTY  FROM TRANSACTION_HISTORY  TH  WITH(NOLOCK)
        INNER JOIN [USER]  U WITH(NOLOCK) ON TH.USER_STAMP=U.[USER_ID]
        LEFT JOIN ITEM I WITH(NOLOCK) ON TH.ITEM=I.ITEM AND i.company= th.company
        WHERE TH.DATE_TIME_STAMP>='{bt}'
        AND  TH.DATE_TIME_STAMP<='{et}'
        AND TRANSACTION_TYPE='收货'
        GROUP BY TH.USER_STAMP,U.DESCRIPTION
        UNION 
        SELECT TH.USER_STAMP+'('+U.DESCRIPTION+')' NAME,0 RECE_QTY,SUM(QUANTITY) PUT_QTY,0 PICK_QTY,0 PACK_QTY,0 COUNTED_QTY,0 M_QTY  FROM TRANSACTION_HISTORY  TH  WITH(NOLOCK)
        INNER JOIN [USER]  U WITH(NOLOCK) ON TH.USER_STAMP=U.[USER_ID]
        LEFT JOIN ITEM I WITH(NOLOCK) ON TH.ITEM=I.ITEM AND i.company= th.company
        WHERE TH.DATE_TIME_STAMP>='{bt}'
        AND  TH.DATE_TIME_STAMP<='{et}'
        AND TRANSACTION_TYPE='上架确认'
        GROUP BY TH.USER_STAMP,U.DESCRIPTION
        UNION 
        SELECT TH.USER_STAMP+'('+U.DESCRIPTION+')' NAME,0 RECE_QTY,0  PUT_QTY,SUM(QUANTITY) PICK_QTY,0 PACK_QTY,0 COUNTED_QTY,0 M_QTY  FROM TRANSACTION_HISTORY  TH  WITH(NOLOCK)
        INNER JOIN [USER]  U WITH(NOLOCK) ON TH.USER_STAMP=U.[USER_ID]
        LEFT JOIN ITEM I WITH(NOLOCK) ON TH.ITEM=I.ITEM AND i.company= th.company
        WHERE TH.DATE_TIME_STAMP>='{bt}'
        AND  TH.DATE_TIME_STAMP<='{et}'
        AND TRANSACTION_TYPE='拣货确认'
        GROUP BY TH.USER_STAMP,U.DESCRIPTION
        UNION
        SELECT SC.OQC_USER+'('+U.DESCRIPTION+')' NAME,0 RECE_QTY,0  PUT_QTY,0 PICK_QTY,SUM(QUANTITY) PACK_QTY,0 COUNTED_QTY,0 M_QTY FROM SHIPPING_CONTAINER SC WITH(NOLOCK)
        LEFT JOIN [USER]  U WITH(NOLOCK) ON SC.OQC_USER=U.[USER_ID]
        LEFT JOIN ITEM I WITH(NOLOCK) ON SC.ITEM=I.ITEM AND SC.COMPANY=I.COMPANY
        WHERE 1=1
        AND STATUS>=800 AND PARENT>0
        AND SC.OQC_START_DATE_TIME>='{bt}'
        AND  SC.OQC_START_DATE_TIME<='{et}'
        GROUP BY  SC.OQC_USER,U.DESCRIPTION
        UNION
        SELECT  CD.COUNTED_BY_USER+'('+U.DESCRIPTION+')' NAME,0 RECE_QTY,0  PUT_QTY,0 PICK_QTY,0 PACK_QTY,SUM(COUNTED_QTY) COUNTED_QTY,0 M_QTY FROM CYCLE_COUNT_DETAIL CD WITH(NOLOCK) 
        LEFT JOIN [USER]  U WITH(NOLOCK) ON CD.COUNTED_BY_USER=U.[USER_ID]
        LEFT JOIN ITEM I WITH(NOLOCK) ON CD.ITEM=I.ITEM  AND  CD.COMPANY=I.COMPANY
        WHERE 1=1
        AND CONDITION!='OPEN'
        AND CD.COUNTED_DATE_TIME>='{bt}'
        AND  CD.COUNTED_DATE_TIME<='{et}'
        GROUP BY  CD.COUNTED_BY_USER,U.DESCRIPTION
        UNION
        SELECT TH.USER_STAMP+'('+U.DESCRIPTION+')' NAME, 0 RECE_QTY,0  PUT_QTY,0 PICK_QTY,0 PACK_QTY,0 COUNTED_QTY,SUM(QUANTITY) M_QTY  FROM TRANSACTION_HISTORY  TH  WITH(NOLOCK)
        INNER JOIN [USER]  U WITH(NOLOCK) ON TH.USER_STAMP=U.[USER_ID]
        LEFT JOIN ITEM I WITH(NOLOCK) ON TH.ITEM=I.ITEM  AND  i.COMPANY=I.COMPANY
        WHERE TH.DATE_TIME_STAMP>='{bt}'
        AND  TH.DATE_TIME_STAMP<='{et}'
        AND TRANSACTION_TYPE='库存移动'
        AND REMARK='库存移动'
        GROUP BY TH.USER_STAMP,U.DESCRIPTION
        ) A
        GROUP BY NAME
        HAVING NAME NOT IN {user}
        ORDER BY NAME
        """.format(bt=btime,et=etime,user=user)

        try:

            cursor.execute(sql)
            row = cursor.fetchone()
            yield_table = {}
            while row:
                name = row[0]   # 姓名
                RECE_QTY = int(row[1])   #收货
                PUT_QTY = int(row[2])    # 上架
                PICK_QTY = int(row[3])   # 拣货
                PACK_QTY = int(row[4])   # 包装
                COUNTED_QTY = int(row[5])    # 盘点
                M_QTY = int(row[6])  # 移库
                yield_table[name] = [RECE_QTY,PUT_QTY,PICK_QTY,PACK_QTY,COUNTED_QTY,M_QTY]
                row = cursor.fetchone()

        # 也可以使用for循环来迭代查询结果
        # for row in cursor:
        # print("ID=%d, Name=%s" % (row[0], row[1]))
        except:
            yield_table = '执行结果出错'
        # 关闭连接
        finally:
            self.db.close()

            return yield_table


    def chayi(self, btiem, etime):

        cursor = self.db.cursor()

        sql = """
        SELECT TASK_ID,ASSIGNED_USER,ITEM,ITEM_DESC,TOTAL_QTY,FROM_QTY,TO_QTY,FROM_LOC,CONDITION,REFERENCE_ID,DATE_TIME_STAMP FROM [dbo].[TASK_DETAIL] WHERE 
        REFERENCE_ID like '%PICK%'  
        AND CONDITION='OPEN'
        AND DATE_TIME_STAMP>='{bt}'
        AND DATE_TIME_STAMP<='{et}'
        """.format(bt=btiem, et=etime)

        # print(sql)

        chayi = [['任务号', '最后操作人','条码','剩余数','货位','拣货单号']]
        try:
            cursor.execute(sql)
            row = cursor.fetchone()

            while row:
                item=[]
                row = cursor.fetchone()
                # print(row)
                item.append(row[0]) # 任务号
                item.append(row[1]) # 最后操作人
                item.append(row[2]) # 条码
                item.append(int(row[5])) # 剩余数
                item.append(row[7]) # 货位
                item.append(row[9]) # 单号
                # print(item)

                chayi.append(item)

        except:
            pass
        finally:
            self.db.close()
            return chayi


    def kc(self,sku):

        cursor = self.db.cursor()

        sql="""
        SELECT LI.WAREHOUSE,LI.COMPANY,LI.LOCATION,LI.ITEM,LI.ITEM_DESC,LI.ON_HAND_QTY,
        LI.IN_TRANSIT_QTY,LI.attribute3,IT.BRAND,
        ALLOCATED_QTY,INVENTORY_STS,IT.ITEM_CATEGORY1,ITEM_CATEGORY2,ITEM_CATEGORY3
         FROM LOCATION_INVENTORY LI
        INNER JOIN ITEM IT
        ON LI.ITEM=IT.ITEM AND LI.COMPANY=IT.COMPANY
        WHERE 1=1 
        AND LI.ITEM='{}'
        """.format(sku)

        sku_item = [['条码', '货位','在库数','已分配数','描述','品牌']]
        try:
            cursor.execute(sql)
            row = cursor.fetchone()

            while row:
                item=[]
                item.append(row[3]) # 条码
                item.append(row[2]) # 货位
                item.append(row[5]) # 在库数
                item.append(row[9]) # 已分配数
                item.append(row[4]) # 描述
                item.append(row[8]) # 品牌

                sku_item.append(item)
                row = cursor.fetchone()
                # print(row)


        except:
            pass
        finally:
            self.db.close()
            return sku_item


    def query_tg(self,brand):
        
        today = datetime.date.today()

        btime = str(today - datetime.timedelta(days=25))
        etime = str(today + datetime.timedelta(days=1))
        brand_name = brand
        brand = '%' + brand + '%'

        cursor = self.db.cursor()

        sql = """
        SELECT SH.COMPANY,SH.SHIP_TO,SHIP_TO_POSTAL_CODE,SH.SHIPMENT_ID,SH.SHIP_TO_EMAIL_ADDRESS,sh.user_def1
        ,SH.INTERNAL_WAVE_NUM,SH.SHIPMENT_TYPE,SH.USER_DEF5,SH.CREATE_DATE_TIME,ISNULL(C.CONC_QTY,0) CONC_QTY, ISNULL(SUM(TD.TOTAL_QTY),0) TOTAL_QTY,ISNULL(SUM(TD.TOTAL_QTY),0)-ISNULL(SUM(TD.FROM_QTY),0) FROM_QTY
        ,ISNULL(B.PACK_QTY,0) PACK_QTY
        FROM SHIPMENT_HEADER SH WITH(NOLOCK) INNER JOIN SHIPMENT_DETAIL SD WITH(NOLOCK)
        ON SH.SHIPMENT_ID=SD.SHIPMENT_ID  LEFT JOIN TASK_DETAIL TD WITH(NOLOCK) ON
        SD.SHIPMENT_ID=TD.REFERENCE_ID AND SD.INTERNAL_SHIPMENT_LINE_NUM=TD.REFERENCE_LINE_NUM
        LEFT JOIN 
        (
        SELECT SHIPMENT_ID,SUM(QUANTITY) PACK_QTY FROM SHIPPING_CONTAINER WITH(NOLOCK) WHERE 1=1 
        AND PARENT>0 AND STATUS>=800 
        GROUP BY SHIPMENT_ID) B  ON SH.SHIPMENT_ID=B.SHIPMENT_ID
        LEFT JOIN 
        (
        SELECT SHIPMENT_ID,COUNT(1) CONC_QTY FROM SHIPPING_CONTAINER WITH(NOLOCK) WHERE 1=1 
        AND PARENT=0 AND STATUS>=800 
        GROUP BY SHIPMENT_ID
        ) C   ON SH.SHIPMENT_ID=C.SHIPMENT_ID
        WHERE 1=1 
        and SH.CREATE_DATE_TIME>='%s'
        AND SH.CREATE_DATE_TIME<='%s'
        AND SHIP_TO_POSTAL_CODE NOT IN %s
        GROUP BY SH.COMPANY,SH.SHIP_TO,SHIP_TO_POSTAL_CODE,SH.SHIPMENT_ID,SH.SHIP_TO_EMAIL_ADDRESS,sh.user_def1
        ,SH.INTERNAL_WAVE_NUM,SH.SHIPMENT_TYPE,SH.USER_DEF5,SH.CREATE_DATE_TIME,B.PACK_QTY,C.CONC_QTY
        HAVING SH.SHIPMENT_TYPE ='B2BSO'
        """ % (btime,etime,str(brand))

  
        cursor = self.db.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()

        zs = 0
        yj = 0
        yb = 0
        # return_text = "品牌|类型|总数|未拣|未包\n"
        while row:
            # return_text = return_text +  row[0] + ',' + row[1] + ',' + str(row[2]) + ',' + str(row[2] - row[3]) + ',' + str(int(row[2] - row[4])) + '\n'
            zs += int(row[11])
            yj += int(row[12])
            yb += int(row[13])
            row = cursor.fetchone()


        return_text = '订单数：' + str(zs) + ",已拣：" + str(yj) + ",已包：" + str(yb) + '\n' + '{} 至 {}'.format(btime[5:],etime[5:])
        return return_text     



if __name__ == '__main__':
    db= WMS('搬仓管理群')

    n =  db.query_rk('北极绒')
    print(n)
    input('jj')
