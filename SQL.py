import pymssql
import datetime


class WMS:

    def __init__(self):
        self.db = pymssql.connect(server="121.9.248.170", port="2466", user="vip", password="vip2015",
                                  database="TTLP_01", charset="UTF-8")

    def query_rk(self, brand):

        today = datetime.date.today()

        btime = str(today - datetime.timedelta(days=7))
        etime = str(today + datetime.timedelta(days=1))

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

        return return_text

    def query_ck(self,batch):

        pc = {
            '4点': ['3:00', '5:00'],
            '11点': ['10:30', '13:00'],
            '15点': ['14:00', '16:30'],
            '19点': ['18:00', '20:00'],
            '23点': ['22:00', '23:59']
        }


        sj = pc.get(batch)

        if not sj:
            return '批次不存在，目前批次有[4点,11点,15点,19点,23点]'



        bt = str(datetime.date.today()) + " " + str(sj[0])

        et = str(datetime.date.today()) + " " + str(sj[1])
        print(bt,et)

        with open('brand.txt', 'r',encoding='utf-8') as fobj:
            brand = fobj.readlines()

        brand = tuple([i.strip('\n') for i in brand])



        sql = """
        SELECT SHIP_TO_POSTAL_CODE,SH.SHIP_TO_EMAIL_ADDRESS,ISNULL(SUM(TD.TOTAL_QTY),0) TOTAL_QTY,ISNULL(SUM(TD.TOTAL_QTY),0)-ISNULL(SUM(TD.FROM_QTY),0) FROM_QTY
        ,ISNULL(B.PACK_QTY,0) PACK_QTY
        FROM SHIPMENT_HEADER SH WITH(NOLOCK) INNER JOIN SHIPMENT_DETAIL SD WITH(NOLOCK)
        ON SH.SHIPMENT_ID=SD.SHIPMENT_ID  LEFT JOIN TASK_DETAIL TD WITH(NOLOCK) ON
        SD.SHIPMENT_ID=TD.REFERENCE_ID AND SD.INTERNAL_SHIPMENT_LINE_NUM=TD.REFERENCE_LINE_NUM
        LEFT JOIN 
        (
        SELECT SHIPMENT_ID,SUM(QUANTITY) PACK_QTY FROM SHIPPING_CONTAINER WITH(NOLOCK) WHERE 1=1 
        AND PARENT>0 AND STATUS>=800 
        GROUP BY SHIPMENT_ID) B  ON SH.SHIPMENT_ID=B.SHIPMENT_ID
        WHERE 1=1 
        and SH.CREATE_DATE_TIME>='%s'
        AND SH.CREATE_DATE_TIME<='%s'
        AND SH.SHIPMENT_TYPE='B2BSO'
        AND SHIP_TO_POSTAL_CODE IN %s
        GROUP BY SHIP_TO_POSTAL_CODE,SH.SHIP_TO_EMAIL_ADDRESS,B.PACK_QTY
        """ % (bt,et,str(brand))



        cursor = self.db.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()

        zs = 0
        yj = 0
        yb = 0
        return_text = "品牌|类型|总数|未拣|未包\n"
        while row:
            return_text = return_text +  row[0] + ',' + row[1] + ',' + \
                          str(row[2]) + ',' + str(row[2] - row[3]) + ',' + str(int(row[2] - row[4])) + '\n'
            zs += row[2]
            yj += row[3]
            yb += row[4]
            row = cursor.fetchone()


        return_text += '总订单数：' + str(zs) + ",已拣：" + str(yj) + ",已包：" + str(yb) + '\n' + '数据依赖品牌消息维护，仅供参考'
        return return_text



    def yield_table(self,btime,etime):


        with open('user.txt', 'r',encoding='utf-8') as fobj:
            user = fobj.readlines()
            user = tuple([i.strip('\n') for i in user])

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
        HAVING NAME IN {user}
        ORDER BY NAME
        """.format(bt=btime,et=etime,user=user)

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

        # 关闭连接
        self.db.close()

        return yield_table