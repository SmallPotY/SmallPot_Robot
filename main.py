import itchat
# import全部消息类型
from itchat.content import *
import SQL
import model
import datetime
import os
# 处理文本类消息
# 包括文本、位置、名片、通知、分享
# @itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
# def text_reply(msg):
#     # 微信里，每个用户和群聊，都使用很长的ID来区分
#     # msg['FromUserName']就是发送者的ID
#     # 将消息的类型和文本内容返回给发送者
#     itchat.send('%s: %s' % (msg['Type'], msg['Text']), msg['FromUserName'])

# # 处理多媒体类消息
# # 包括图片、录音、文件、视频
# @itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
# def download_files(msg):
#     # msg['Text']是一个文件下载函数
#     # 传入文件名，将文件下载下来
#     msg['Text'](msg['FileName'])
#     # 把下载好的文件再发回给发送者
#     return '@%s@%s' % ({'Picture': 'img', 'Video': 'vid'}.get(msg['Type'], 'fil'), msg['FileName'])

# # 处理好友添加请求
# @itchat.msg_register(FRIENDS)
# def add_friend(msg):
#     # 该操作会自动将新好友的消息录入，不需要重载通讯录
#     itchat.add_friend(**msg['Text'])
#     # 加完好友后，给好友打个招呼
#     itchat.send_msg('Nice to meet you!', msg['RecommendInfo']['UserName'])}

# 处理群聊消息
'''
msg['User']['NickName']     群昵称
msg['FromUserName']         群ID
msg['ActualNickName']       发送人
msg['Content']              发送内容
msg['CreateTime']           时间戳
'''


@itchat.msg_register(TEXT, isGroupChat=True)
def text_reply(msg):
    Content = msg['Text']
    NickName = msg['User']['NickName']
    if NickName in ['搬仓管理群','华中管理层沟通群']:
        if '查询进度=' in Content:
            brand = Content.replace("查询进度=", "")
            itchat.send('{}入库进度查询中'.format(brand), msg['FromUserName'])
            query = SQL.WMS(NickName)
            return_content = query.query_rk(brand)
            itchat.send(return_content, msg['FromUserName'])

        if '查询出货=' in Content:
            batch = Content.replace("查询出货=", "")
            query = SQL.WMS(NickName)

            batch = batch.split('.')


            if len(batch) !=2:
                itchat.send("查询参数不符，参数格式：开始时间.结束时间", msg['FromUserName'])
                return
            jday = datetime.datetime.now()
            qday = datetime.datetime.now() + datetime.timedelta(days=-1)
            jday = jday.strftime('%Y-%m-%d')
            qday = qday.strftime('%Y-%m-%d')


            if int(batch[0]) < 0:
                btime = qday + " " + str(abs(int(batch[0]))) + ":00"
            else:
                btime = jday + " " + str(abs(int(batch[0]))) + ":00"

            etime = jday + " " + str(abs(int(batch[1]))) + ":00"
            print(btime,etime)
            return_content = query.query_ck(btime,etime)
            itchat.send(return_content, msg['FromUserName'])

        if '查询产量=' in Content:

            work_type = Content.replace("查询产量=", "")
            work_type = work_type.split('.')
            print(work_type)
            if len(work_type) != 3:
                itchat.send("查询参数不符，参数格式：开始时间.结束时间.操作类型", msg['FromUserName'])
                return

            jday = datetime.datetime.now()
            qday = datetime.datetime.now() + datetime.timedelta(days=-1)
            jday = jday.strftime('%Y-%m-%d')
            qday = qday.strftime('%Y-%m-%d')

            if int(work_type[0]) < 0:
                btime = qday + " " + str(abs(int(work_type[0]))) + ":00"
            else:
                btime = jday + " " + str(abs(int(work_type[0]))) + ":00"

            etime = jday + " " + str(abs(int(work_type[1]))) + ":00"

            itchat.send("{}至{},{}产量查询中".format(btime, etime, work_type[2]), msg['FromUserName'])

            fname = datetime.datetime.now()
            fname = fname.strftime('%Y%m%d%H%I%M%S') + ".png"

            n = model.yield_type(btime, etime, work_type[2], fname,NickName)
            
            if n == "操作类型不存在！目前可供查询：收货,上架,拣货,包装,盘点,移库":
                itchat.send(n, msg['FromUserName'])
            else:
                itchat.send_image(fname, msg['FromUserName'])
                os.remove(fname)



        if '拣货差异=' in Content:
            batch = Content.replace("拣货差异=", "")
            query = SQL.WMS(NickName)

            batch = batch.split('.')

            if len(batch) !=2:
                itchat.send("查询参数不符，参数格式：开始时间.结束时间", msg['FromUserName'])
                return
                
            jday = datetime.datetime.now()
            qday = datetime.datetime.now() + datetime.timedelta(days=-1)
            jday = jday.strftime('%Y-%m-%d')
            qday = qday.strftime('%Y-%m-%d')

            if int(batch[0]) < 0:
                btime = qday + " " + str(abs(int(batch[0]))) + ":00"
            else:
                btime = jday + " " + str(abs(int(batch[0]))) + ":00"

            etime = jday + " " + str(abs(int(batch[1]))) + ":00"

            row = query.chayi(btime,etime)
            if len(row)==1:
                itchat.send('拣货已完成', msg['FromUserName'])
                return
            else:
                itchat.send('拣货差异生成中', msg['FromUserName'])
                model.chayi(row)
                itchat.send_image('CHAYI.PNG', msg['FromUserName'])
                os.remove('CHAYI.PNG')


        if '条码库存=' in Content:
            batch = Content.replace("条码库存=", "")
            query = SQL.WMS(NickName)

            row = query.kc(batch)

            if len(row) == 1:
                itchat.send('{}查无库存'.format(batch), msg['FromUserName'])
                return
            else:
                model.chayi(row)
                itchat.send_image('CHAYI.PNG', msg['FromUserName'])
                os.remove('CHAYI.PNG')



# 在auto_login()里面提供一个True，即hotReload=True
# 即可保留登陆状态
# 即使程序关闭，一定时间内重新开启也可以不用重新扫码
itchat.auto_login(hotReload=True)
# itchat.auto_login(hotReload=True)
itchat.run()
