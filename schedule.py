from ortools.sat.python import cp_model
import pprint
import numpy as np

pp = pprint.PrettyPrinter()

# APN
# A: 8-16, P: 16-24, N: 0-8,
# 0: N, 1: A, 2: P
NUM_SHIFTS = 3  # 固定值

num_weeks = 1  # 排班以周为最小单位

num_days = 7 * num_weeks
total_shifts = num_days * NUM_SHIFTS


def solve_schedule(num_nurses, args):
    print(args)
    model = cp_model.CpModel()
    shifts = {}

    # 创建shift变量
    for n in range(num_nurses):
        for d in range(num_days):
            for s in range(NUM_SHIFTS):
                s_number = d * NUM_SHIFTS + s
                shifts[(n, s_number)] = model.NewBoolVar(f'shift_n{n}s{s_number}')
                model.AddHint(shifts[(n, s_number)], np.random.randint(0, 2))  # 设置随机初始值, 或者设置预设值


    num_workday_n = args.get("num_workday_n", 0)
    num_workday_a = args.get("num_workday_a", 0)
    num_workday_p = args.get("num_workday_p", 0)

    num_weekend_n = args.get("num_weekend_n", 0)
    num_weekend_a = args.get("num_weekend_a", 0)
    num_weekend_p = args.get("num_weekend_p", 0)

    for w in range(num_weeks):

        # Sunday
        model.Add(sum(shifts[(n, (w * 7 + 6) * NUM_SHIFTS)] for n in range(num_nurses)) == num_weekend_n)  # N
        model.Add(sum(shifts[(n, (w * 7 + 6) * NUM_SHIFTS + 1)] for n in range(num_nurses)) == num_weekend_a)  # A
        model.Add(sum(shifts[(n, (w * 7 + 6) * NUM_SHIFTS + 2)] for n in range(num_nurses)) == num_weekend_p)  # P

        # work day
        for d in range(5):
            model.Add(sum(shifts[(n, (w * 7 + d) * NUM_SHIFTS)] for n in range(num_nurses)) == num_workday_n)  # N
            model.Add(sum(shifts[(n, (w * 7 + d) * NUM_SHIFTS + 1)] for n in range(num_nurses)) >= num_workday_a)  # A
            model.Add(sum(shifts[(n, (w * 7 + d) * NUM_SHIFTS + 2)] for n in range(num_nurses)) >= num_workday_p)  # P

        # Saturday
        model.Add(sum(shifts[(n, (w * 7 + 5) * NUM_SHIFTS)] for n in range(num_nurses)) == num_weekend_n)  # N
        model.Add(sum(shifts[(n, (w * 7 + 5) * NUM_SHIFTS + 1)] for n in range(num_nurses)) == num_weekend_a)  # A
        model.Add(sum(shifts[(n, (w * 7 + 5) * NUM_SHIFTS + 2)] for n in range(num_nurses)) == num_weekend_p)  # P

    # 每天最多一个班次
    for n in range(num_nurses):
        for d in range(num_days):
            model.Add(sum(shifts[(n,d * NUM_SHIFTS + i)] for i in range(NUM_SHIFTS)) <= 1) #5 shifts each week

    # 每周5天
    for n in range(num_nurses):
        for w in range(num_weeks):
            model.Add(sum(shifts[(n, w * 7 * NUM_SHIFTS + ds)] for ds in range(7*NUM_SHIFTS)) <= 5) #5 shifts each week

    # A班后至少休几个班次

    extra_rest_constrain = args.get("extra_rest_constrain", False)

    if extra_rest_constrain:
        extra_rest_n = args.get("extra_rest_n", 3)
        extra_rest_a = args.get("extra_rest_a", 1)
        extra_rest_p = args.get("extra_rest_p", 1)
        for n in range(num_nurses):
            for ts in range(0, total_shifts - NUM_SHIFTS, NUM_SHIFTS):  # N班
                model.Add(sum([shifts[(n, ts + i)] for i in range(0, extra_rest_n + 1)]) <= 1)
            for ts in range(1, total_shifts - NUM_SHIFTS, NUM_SHIFTS):  # A班
                model.Add(sum([shifts[(n, ts + i)] for i in range(0, extra_rest_a + 1)]) <= 1)
            for ts in range(2, total_shifts - NUM_SHIFTS, NUM_SHIFTS):  # P班
                model.Add(sum([shifts[(n, ts + i)] for i in range(0, extra_rest_p + 1)]) <= 1)

    max_work_nights = model.NewIntVar(0, num_days, 'max_work_nights')
    min_work_nights = model.NewIntVar(0, num_days, 'min_work_nights')

    work_nights = [sum(shifts[(n, d * NUM_SHIFTS)] for d in range(num_days)) for n in range(num_nurses)]

    model.AddMaxEquality(max_work_nights, work_nights)
    model.AddMinEquality(min_work_nights, work_nights)

    # model.Minimize((max_work_nights - min_work_nights)*10 + (max_work_days - min_work_days) * 10  )
    model.Minimize((max_work_nights - min_work_nights) )

    # for n in range(num_nurses):
    #     for w in range(0, num_weeks):  # 每周
    #         model.Add(sum([shifts[(n, w * 7 * NUM_SHIFTS + ts)] for ts in range(0, 7 * NUM_SHIFTS)]) < 5)
            #         model.Add(sum([shifts[(n, w * 7 + d)] for d in range(0,7)]) >= 4)

    solver = cp_model.CpSolver()
    #solver.parameters.num_search_workers = 8
    solver.parameters.cp_model_presolve = False

    status = solver.Solve(model)
    r_shifts = {}
    if status == cp_model.OPTIMAL:
        # for n in range(num_nurses):
        #     for d in range(num_days):
        #         for s in range(NUM_SHIFTS):
        #             s_number = d * NUM_SHIFTS + s
        #             r_shifts[(n, s_number)] =  solver.BooleanValue(shifts[(n, d * NUM_SHIFTS + s)])
        # print(r_shifts)
        #schedule = [[[0 for _ in range(NUM_SHIFTS)] for _ in range(num_days)] for _ in range(num_nurses)]
        schedule = np.zeros((num_nurses, num_days))
        for d in range(num_days):
            for s in range(NUM_SHIFTS):
                for n in range(num_nurses):
                    if solver.BooleanValue(shifts[(n, d * NUM_SHIFTS + s)]):
                        schedule[n][d] += 10**s
        return schedule
    else:
        return None
