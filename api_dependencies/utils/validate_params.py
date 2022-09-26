def start_end_check(start, end, article_num):
    """
    检查start、end的合法性：
    1、article_num必须小于等于1000：article_num<=1000
    2、end如果为-1，则取文章数作为end
    3、start必须大于等于0且小于end：0<=start<end
    4、end必须小于等于文章数：end<=article_num
    :return:
    """
    message = ""
    article_num = min(article_num, 1000)

    if end == -1:
        end = article_num
    elif end > article_num:
        end = article_num

    if start < 0 or start >= end:
        message = "start error"

    return start, end, message


def test():
    import random
    start = [random.randint(-100, 1500) for _ in range(2000)]
    end = [random.randint(-100, 1500) for _ in range(2000)]
    article_num = [random.randint(0, 1500) for _ in range(2000)]
    success = 0
    error = 0
    for i in range(2000):
        # print(start[i], end[i], article_num[i])
        s, e, m = start_end_check(start[i], end[i], article_num[i])
        if not m:
            if s >= 0 and s < e and e <= article_num[i] and e <= 1000:
                success += 1
            else:
                print(start[i], end[i])
                print(s, e)
                print("\n")
        else:
            error += 1
    print(success, error, success + error)


if __name__ == '__main__':
    test()