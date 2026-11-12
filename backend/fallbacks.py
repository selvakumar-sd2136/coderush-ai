"""Built-in problems: 7 topics x 3 levels. Expected outputs are computed from each reference solution."""
import copy

def _P(topic, level, title, statement, sig, ref, inputs):
    return dict(topic=topic, level=level, title=title, statement=statement, sig=sig, ref=ref, inputs=inputs)

PROBLEMS = [
# ---------------- Arrays ----------------
_P("Arrays","Easy","Two Sum","Given a list of integers nums and an integer target, return the indices [i, j] (i smaller than j) of the two numbers that add up to target. Exactly one solution exists and you may not use the same element twice.","nums, target","""def solution(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
""",[[[2,7,11,15],9],[[3,2,4],6],[[3,3],6],[[1,5,8,3],11],[[-1,-2,-3,-4,-5],-8]]),
_P("Arrays","Medium","Maximum Subarray Sum","Given a list of integers nums, return the largest sum of any contiguous, non-empty sub-list.","nums","""def solution(nums):
    best = cur = nums[0]
    for n in nums[1:]:
        cur = max(n, cur + n)
        best = max(best, cur)
    return best
""",[[[-2,1,-3,4,-1,2,1,-5,4]],[[1]],[[5,4,-1,7,8]],[[-3,-2,-1]],[[2,-1,2,-1,2]]]),
_P("Arrays","Hard","Longest Increasing Subsequence","Given a list of integers nums, return the length of the longest strictly increasing subsequence (elements need not be adjacent). Aim for better than O(n^2).","nums","""import bisect
def solution(nums):
    tails = []
    for n in nums:
        i = bisect.bisect_left(tails, n)
        if i == len(tails):
            tails.append(n)
        else:
            tails[i] = n
    return len(tails)
""",[[[10,9,2,5,3,7,101,18]],[[0,1,0,3,2,3]],[[7,7,7,7]],[[1,2,3,4,5]],[[5,4,3,2,1]]]),
# ---------------- Strings ----------------
_P("Strings","Easy","Palindrome Check","Return True if the string s reads the same forwards and backwards, otherwise False.","s","""def solution(s):
    return s == s[::-1]
""",[["madam"],["hello"],["a"],["abca"],["racecar"]]),
_P("Strings","Medium","Longest Substring Without Repeating Characters","Given a string s, return the length of the longest substring that contains no repeated characters.","s","""def solution(s):
    last, start, best = {}, 0, 0
    for i, ch in enumerate(s):
        if ch in last and last[ch] >= start:
            start = last[ch] + 1
        last[ch] = i
        best = max(best, i - start + 1)
    return best
""",[["abcabcbb"],["bbbbb"],["pwwkew"],[""],["abcdef"]]),
_P("Strings","Hard","Longest Palindromic Substring Length","Given a string s, return the length of the longest substring of s that is a palindrome.","s","""def solution(s):
    best = 0
    for c in range(len(s)):
        for l, r in ((c, c), (c, c + 1)):
            while l >= 0 and r < len(s) and s[l] == s[r]:
                l -= 1
                r += 1
            best = max(best, r - l - 1)
    return best
""",[["babad"],["cbbd"],["a"],["forgeeksskeegfor"],["abcde"]]),
# ---------------- Loops ----------------
_P("Loops","Easy","Sum of Even Numbers","Given a list of integers, return the sum of all the even numbers in it.","nums","""def solution(nums):
    return sum(n for n in nums if n % 2 == 0)
""",[[[1,2,3,4]],[[]],[[7,9]],[[2,2,2]],[[-2,5,10]]]),
_P("Loops","Medium","Count Primes","Given a non-negative integer n, return how many prime numbers are strictly less than n.","n","""def solution(n):
    if n < 3:
        return 0
    s = [True] * n
    s[0] = s[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            for j in range(i * i, n, i):
                s[j] = False
    return sum(s)
""",[[10],[0],[2],[30],[100]]),
_P("Loops","Hard","Longest Collatz Chain","For a start number, repeat: if even divide by 2, if odd multiply by 3 and add 1, until you reach 1. The chain length counts every number including the start and the final 1. Given limit, return the start number between 1 and limit-1 that gives the longest chain (smallest start if tied).","limit","""def solution(limit):
    best, best_len = 1, 0
    for s in range(1, limit):
        n, c = s, 1
        while n != 1:
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            c += 1
        if c > best_len:
            best, best_len = s, c
    return best
""",[[10],[2],[30],[100],[1000]]),
# ---------------- Sorting ----------------
_P("Sorting","Easy","Kth Smallest Element","Given a list of integers nums and an integer k (counting from 1), return the k-th smallest element.","nums, k","""def solution(nums, k):
    return sorted(nums)[k - 1]
""",[[[7,3,9,1],2],[[5],1],[[4,4,1],2],[[9,8,7],3],[[-1,-5,2],1]]),
_P("Sorting","Medium","Merge Intervals","Given a list of [start, end] intervals, merge all overlapping (or touching) intervals and return the merged list sorted by start.","intervals","""def solution(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
""",[[[[1,3],[2,6],[8,10],[15,18]]],[[[1,4],[4,5]]],[[[1,4],[0,4]]],[[[5,6]]],[[[1,10],[2,3],[4,5]]]]),
_P("Sorting","Hard","Count Inversions","An inversion is a pair of positions i < j with nums[i] greater than nums[j]. Given nums, return the number of inversions. Aim for O(n log n) using merge sort.","nums","""def solution(nums):
    c = 0
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] > nums[j]:
                c += 1
    return c
""",[[[2,4,1,3,5]],[[1,2,3]],[[3,2,1]],[[1,20,6,4,5]],[[]]]),
# ---------------- Searching ----------------
_P("Searching","Easy","Binary Search","Given a sorted list nums and a target, return the index of target, or -1 if it is not present.","nums, target","""def solution(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        m = (lo + hi) // 2
        if nums[m] == target:
            return m
        if nums[m] < target:
            lo = m + 1
        else:
            hi = m - 1
    return -1
""",[[[1,3,5,7],5],[[1,3,5,7],4],[[2],2],[[],1],[[1,2,3,4,5,6],6]]),
_P("Searching","Medium","Search in Rotated Sorted Array","A sorted list of distinct integers was rotated at an unknown pivot (for example [4,5,6,7,0,1,2]). Return the index of target, or -1 if absent. Aim for O(log n).","nums, target","""def solution(nums, target):
    return nums.index(target) if target in nums else -1
""",[[[4,5,6,7,0,1,2],0],[[4,5,6,7,0,1,2],3],[[1],0],[[1],1],[[3,1],1]]),
_P("Searching","Hard","Minimum Eating Speed","Piles of bananas are given in piles. You must eat all of them within h hours; each hour you pick one pile and eat up to k bananas from it (finishing a pile early wastes the rest of that hour). Return the smallest integer k that works. Use binary search on k.","piles, h","""def solution(piles, h):
    lo, hi = 1, max(piles)
    while lo < hi:
        m = (lo + hi) // 2
        if sum((p + m - 1) // m for p in piles) <= h:
            hi = m
        else:
            lo = m + 1
    return lo
""",[[[3,6,7,11],8],[[30,11,23,4,20],5],[[30,11,23,4,20],6],[[1],1],[[312884470],312884469]]),
# ---------------- Hashing ----------------
_P("Hashing","Easy","First Repeated Element","Return the first element whose second occurrence is met earliest while scanning left to right; return -1 if no element repeats.","nums","""def solution(nums):
    seen = set()
    for n in nums:
        if n in seen:
            return n
        seen.add(n)
    return -1
""",[[[3,1,3,1]],[[1,2,3]],[[5,5]],[[1,2,2,1]],[[]]]),
_P("Hashing","Medium","Longest Consecutive Sequence","Given an unsorted list of integers, return the length of the longest run of consecutive values (for example 1,2,3,4). Aim for O(n) using a set.","nums","""def solution(nums):
    s = set(nums)
    best = 0
    for n in s:
        if n - 1 not in s:
            m = n
            while m + 1 in s:
                m += 1
            best = max(best, m - n + 1)
    return best
""",[[[100,4,200,1,3,2]],[[0,3,7,2,5,8,4,6,0,1]],[[]],[[1,1,1]],[[9,1,4,7,3,2]]]),
_P("Hashing","Hard","Subarray Sum Equals K","Given a list of integers nums (may contain negatives) and an integer k, return the number of contiguous sub-lists whose sum equals k. Use prefix sums with a dictionary.","nums, k","""def solution(nums, k):
    seen = {0: 1}
    t = c = 0
    for n in nums:
        t += n
        c += seen.get(t - k, 0)
        seen[t] = seen.get(t, 0) + 1
    return c
""",[[[1,1,1],2],[[1,2,3],3],[[1,-1,0],0],[[3,4,7,2,-3,1,4,2],7],[[1],5]]),
# ---------------- Recursion ----------------
_P("Recursion","Easy","Factorial","Return n! (the factorial of n) using recursion. Assume n is between 0 and 12.","n","""def solution(n):
    return 1 if n <= 1 else n * solution(n - 1)
""",[[5],[0],[1],[10],[3]]),
_P("Recursion","Medium","Count Subsets With Target Sum","Given a list of positive integers nums and a target, return how many subsets (choosing each element at most once, order does not matter, subsets differ by position) add up to target. The empty subset counts when target is 0.","nums, target","""def solution(nums, target):
    def go(i, t):
        if i == len(nums):
            return 1 if t == 0 else 0
        return go(i + 1, t) + go(i + 1, t - nums[i])
    return go(0, target)
""",[[[1,2,3],3],[[1,1,1,1],2],[[5],5],[[2,4,6],5],[[],0]]),
_P("Recursion","Hard","N-Queens Count","Place n queens on an n by n chessboard so that no two attack each other (same row, column or diagonal). Return the number of distinct valid arrangements. Use backtracking.","n","""def solution(n):
    cols, d1, d2 = set(), set(), set()
    def go(r):
        if r == n:
            return 1
        t = 0
        for c in range(n):
            if c in cols or r - c in d1 or r + c in d2:
                continue
            cols.add(c); d1.add(r - c); d2.add(r + c)
            t += go(r + 1)
            cols.discard(c); d1.discard(r - c); d2.discard(r + c)
        return t
    return go(0)
""",[[1],[4],[5],[6],[8]]),
]

def _build(p):
    ns = {}
    exec(p["ref"], ns)
    fn = ns["solution"]
    tests = [{"input": a, "expected": fn(*copy.deepcopy(a))} for a in p["inputs"]]
    names = [x.strip() for x in p["sig"].split(",")]
    ex_in = ", ".join(f"{n} = {v!r}" for n, v in zip(names, tests[0]["input"]))
    return {"title": p["title"], "statement": p["statement"],
            "examples": [{"input": ex_in, "output": repr(tests[0]["expected"])}],
            "starter_code": f"def solution({p['sig']}):\n    # Write your code here\n    pass\n",
            "test_cases": tests, "reference_solution": p["ref"]}

BUILT = {(p["topic"], p["level"]): _build(p) for p in PROBLEMS}

def get(topic, level):
    q = BUILT.get((topic, level))
    return copy.deepcopy(q) if q else None
