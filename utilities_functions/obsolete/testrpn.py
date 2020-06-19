__author__ = 'viking'
from utilities import parse_rpn

if __name__ == '__main__':
    a = "Wf123-TG__C10_R10_DV1_2F_D31_foc.xls"
    b = "2F     D31 and"
    c = "C11"
    e = "C1a 33 or D31 DV1 and and"
    print("b ", parse_rpn(expression=b,targetfilename=a))
    print("c ", parse_rpn(expression=c,targetfilename=a))
    print("e ", parse_rpn(expression=e,targetfilename=a))