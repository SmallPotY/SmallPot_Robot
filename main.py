import pandas as pd
import numpy as np
import pyodbc
from texttable import Texttable
from prettytable import PrettyTable
from PIL import Image, ImageDraw, ImageFont
import itchat
from itchat.content import *

def getData():
    DBfile = r"D:\→共享文件←\小宝财务通\db.accdb"  # 数据库文件
    conn = pyodbc.connect(r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DBfile + ";Uid=;Pwd=;")
     
    data = {
        "事件编号":[],
        "出入账单日期":[],
        "业务发生日期":[],
        "账户":[],
        "项目":[],
        "类型":[],
        "内容":[],
        "科目":[],
        "收入":[],
        "支出":[],
        "收款人":[],
        "备注":[]
    }
    cursor = conn.cursor()
    SQL = "SELECT * from 流水 where status='1';"
    for row in cursor.execute(SQL):
        data['事件编号'].append(row[1])
        data['出入账单日期'].append(row[2])
        data['业务发生日期'].append(row[3])
        data['账户'].append(row[4])   
        data['项目'].append(row[5])   
        data['类型'].append(row[6])   
        data['内容'].append(row[7])   
        data['科目'].append(row[8])
        data['收款人'].append(row[11])  
        data['备注'].append(row[12])    
        tmp_s = row[9] 
        tmp_z = row[10]
        if tmp_s:
            tmp_s = float(tmp_s)
        else:
            tmp_s=0
            
        if tmp_z:
            tmp_z = float(tmp_z)
        else:
            tmp_z=0
        data['收入'].append(tmp_s) 
        data['支出'].append(tmp_z) 
    cursor.close()
    conn.close()

    return data



def statistics(data,tag='账户'):
    
    
#    pd.set_option('display.max_columns',5, 'display.max_rows', 100)
    pd.set_option('display.float_format', lambda x: '%.3f' % x)
    

    df = pd.DataFrame({'类型': data[tag],
                       '支出': data['支出'],
                       '收入': data['收入']})
    
    df['盈利'] = df['支出'] + df['收入']
    df['盈亏'] = df['盈利']/df['收入']
    

    
    t = pd.pivot_table(df, index=['类型'],values=['支出','收入','盈利'],aggfunc=np.sum,fill_value = 0)
    t['盈亏/收入'] =( t['盈利']/t['收入'] ) 
    t['盈亏/收入'] = t['盈亏/收入'].apply(lambda x: format(x, '.2%'))
#    t['账户'] = t.index
    t.insert(0,'类型',t.index)
    return t



def drawing(tab_info):

#
    space = 5


    font = ImageFont.truetype(r'C:\Windows\Fonts\SIMHEI.TTF', 24, encoding='utf-8')
    # Image模块创建一个图片对象
    im = Image.new('RGB', (10, 10), (255, 255, 255))
    # ImageDraw向图片中进行操作，写入文字或者插入线条都可以
    draw = ImageDraw.Draw(im, "RGB")
    # 根据插入图片中的文字内容和字体信息，来确定图片的最终大小
    img_size = draw.multiline_textsize(tab_info, font=font)  # 设置字体才能显示中文
    # 图片初始化的大小为10-10，现在根据图片内容要重新设置图片的大小
    im_new = im.resize((img_size[0] + space * 2, img_size[1] + space * 2))
    del draw
    del im
    draw = ImageDraw.Draw(im_new, 'RGB')
    # 批量写入到图片中，这里的multiline_text会自动识别换行符
    draw.multiline_text((space, space), tab_info, fill=(0, 0, 0), font=font)

    im_new.save('img.PNG', "PNG")
    del draw




#@itchat.msg_register(TEXT, isGroupChat=True)
#def text_reply(msg):
#    Content = msg['Text']
#    NickName = msg['User']['NickName']
#    if NickName in ['小宝三号']:
#        
#        msg = "收到消息:" + Content
#        print(msg['FromUserName'])
#        itchat.send(msg,msg['FromUserName'])
##        if '条码库存=' in Content:
##            batch = Content.replace("条码库存=", "")
##            query = SQL.WMS(NickName)
##            row = query.kc(batch)
##            if len(row) == 1:
##                itchat.send('{}查无库存'.format(batch), msg['FromUserName'])
##                return
##            else:
##                model.chayi(row)
##                itchat.send_image('CHAYI.PNG', msg['FromUserName'])
##                os.remove('CHAYI.PNG')


def getDrawData(data_type):
    data =getData()
    df = statistics(data,data_type)
    
    tb=Texttable()
    tb.set_cols_align(['i','i','i','i','i'])
    tb.set_cols_dtype(['i','i','i','i','i'])
    
    body = [list(df.columns.get_values())]
    
    for i in list(df.values):
        tmp = []
        for j in i:
            tmp.append(j)
        body.append(tmp)
    tb.header(df.columns.get_values())

    tb.add_rows(df.values,header=False)

    drawing(tb.draw())
        

@itchat.msg_register(TEXT, isGroupChat=True)
def text_reply(msg):
    Content = msg['Text']
    NickName = msg['User']['NickName']
    if NickName in ['小宝三号']:
        if '银行收支' in Content:
            getDrawData('账户')
#            itchat.send('蛤??', msg['FromUserName'])
            itchat.send_image('img.PNG', msg['FromUserName'])
#            itchat.send('蛤蛤蛤蛤???', msg['FromUserName'])
        if '项目收支' in Content:
            getDrawData('项目')
#            itchat.send('蛤??', msg['FromUserName'])
            itchat.send_image('img.PNG', msg['FromUserName'])


if __name__ == '__main__':
    
  
    
#    itchat.auto_login(True)
    itchat.auto_login(enableCmdQR=True)
    itchat.run(True)
    

 
    
