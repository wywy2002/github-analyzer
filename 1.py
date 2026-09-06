import sys
#推送11
input = sys.stdin.readline

n = int(input())
s = input().strip()

base = n + 1

# 线段树：查询区间内字典序最小字符，
# 若字符相同则取最靠右的位置
size = 1
while size < n:
    size <<= 1

INF = 10**30
tree = [INF] * (size * 2)

for i, ch in enumerate(s):
    tree[size + i] = (ord(ch) - ord('a')) * base + (n - 1 - i)

for i in range(size - 1, 0, -1):
    tree[i] = min(tree[i * 2], tree[i * 2 + 1])


def query(l, r):
    l += size
    r += size + 1
    res = INF

    while l < r:
        if l & 1:
            res = min(res, tree[l])
            l += 1

        if r & 1:
            r -= 1
            res = min(res, tree[r])

        l >>= 1
        r >>= 1

    return res


max_run = 0
cur_run = 0

for i in range(n):

    # i 作为左侧交换位置时，k 的最大值
    k1 = (n - i - 2) // 2
    k1 = max(k1, 0)

    # i 作为右侧交换位置时，
    # 前面必须存在相同字符组成的可用区间
    span = max_run - 1 if max_run > 0 else 0
    k2 = min(span, n - 1 - i)

    max_k = max(k1, k2)

    if max_k > 0:
        value = query(i + 1, i + max_k)

        min_char = value // base

        if min_char < ord(s[i]) - ord('a'):
            pos = n - 1 - (value % base)
            k = pos - i

            can_left = k <= k1
            can_right = k <= k2

            ans = []

            # 第二种情况：前面的交换字符相同，相当于只交换 i 和 i+k
            if can_right:
                t = list(s)
                t[i], t[i + k] = t[i + k], t[i]
                ans.append(''.join(t))

            # 第一种情况：i 与 i+k 交换，然后寻找最优的第二次交换
            if can_left:
                end = n - k - 1

                best_j = -1
                equal_j = -1

                for j in range(i + k + 1, end + 1):
                    if s[j + k] < s[j]:
                        best_j = j
                        break

                    if s[j + k] == s[j] and equal_j == -1:
                        equal_j = j

                if best_j == -1:
                    if equal_j != -1:
                        best_j = equal_j
                    else:
                        best_j = end

                t = list(s)

                t[i], t[i + k] = t[i + k], t[i]
                t[best_j], t[best_j + k] = t[best_j + k], t[best_j]

                ans.append(''.join(t))

            print(min(ans))
            sys.exit()

    if i == 0 or s[i] != s[i - 1]:
        cur_run = 1
    else:
        cur_run += 1

    max_run = max(max_run, cur_run)

print(s)