# coding=utf-8
import numpy as np
import SQL
import matplotlib.pyplot as plt
import re


def yield_type(btime, etime, work_type, fname):
    lx = {
        '收货': [],
        '上架': [],
        '拣货': [],
        '包装': [],
        '盘点': [],
        '移库': []
    }

    if work_type not in lx:
        return "操作类型不存在！目前可供查询：收货,上架,拣货,包装,盘点,移库"

    db = SQL.WMS()

    data = db.yield_table(btime, etime)

    user = []
    for k, v in data.items():
        name = re.findall(re.compile(r'[(](.*?)[)]', re.S), k)
        user.append(name[0])
        lx['收货'].append(v[0])
        lx['上架'].append(v[1])
        lx['拣货'].append(v[2])
        lx['包装'].append(v[3])
        lx['盘点'].append(v[4])
        lx['移库'].append(v[5])

    sj = lx[work_type]

    user_list = []  # 图表姓名
    cl = []  # 对应产量
    for i, j in enumerate(sj):
        if j:
            user_list.append(user[i])
            cl.append(j)

    loan_grade = cl
    # 图表字体为华文细黑，字号为15
    plt.rc('font', family='STXihei', size=20)

    # 创建柱状图，数据源x,y来源，设置颜色，透明度和外边框颜色
    plt.bar(user_list, loan_grade, color='#99CC01', alpha=0.8, align='center', edgecolor='white')
    # 设置x轴标签
    # plt.xlabel('账号')
    # 设置y周标签
    # plt.ylabel('产量')
    # 设置图表标题
    plt.title("{}——{}/{}产量表".format(btime, etime, work_type))
    # 设置图例的文字和在图表中的位置
    # plt.legend(['产量'], loc='upper right')

    # 设置背景网格线的颜色，样式，尺寸和透明度
    plt.grid(color='#95a5a6', linestyle='--', linewidth=1, axis='y', alpha=0.4)
    plt.xticks(rotation=45)  # 轴标签倾斜度数

    # 循环，为每个柱形添加文本标注
    # 居中对齐
    for x, y in zip(user_list, loan_grade):
        plt.text(x, y + 0.1, str(y), ha='center')

    # 显示图表
    # plt.show()

    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)  # 设置保存大小

    plt.savefig(fname, dpi=200)  # 保存，dip参数设置分辨率
    plt.close('all')  # 关闭图表释放内存


if __name__ == '__main__':
    lx = input('输入类型')
    n = yield_type('2018-6-14 8:00', '2018-6-15 8:00', lx, 'fname.png')
