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
    model = cp_model.CpModel()
    shifts = {}

    # 创建shift变量
    for n in range(num_nurses):
        for d in range(num_days):
            for s in range(NUM_SHIFTS):
                s_number = d * NUM_SHIFTS + s
                shifts[(n, s_number)] = model.NewBoolVar(f'shift_n{n}s{s_number}')
                model.AddHint(shifts[(n, s_number)], np.random.randint(0, 2))  # 设置随机初始值, 或者设置预设值

    # A2,P2,N1 work_days; A1,P1,N1 work_days;
    # for ts in range(0, total_shifts, NUM_SHIFTS):
    #     model.Add(sum(shifts[(n, ts)] for n in range(num_nurses)) == 1) #N
    #     model.Add(sum(shifts[(n, ts + 1)] for n in range(num_nurses)) >= 2) #A
    #     model.Add(sum(shifts[(n, ts + 2)] for n in range(num_nurses)) >= 2) #P

    for w in range(num_weeks):

        # Sunday
        model.Add(sum(shifts[(n, (w * 7 + 6) * NUM_SHIFTS)] for n in range(num_nurses)) == 2)  # N
        model.Add(sum(shifts[(n, (w * 7 + 6) * NUM_SHIFTS + 1)] for n in range(num_nurses)) == 2)  # A
        model.Add(sum(shifts[(n, (w * 7 + 6) * NUM_SHIFTS + 2)] for n in range(num_nurses)) == 2)  # P

        # work day
        for d in range(5):
            model.Add(sum(shifts[(n, (w * 7 + d) * NUM_SHIFTS)] for n in range(num_nurses)) == 2)  # N
            model.Add(sum(shifts[(n, (w * 7 + d) * NUM_SHIFTS + 1)] for n in range(num_nurses)) >= 5)  # A
            model.Add(sum(shifts[(n, (w * 7 + d) * NUM_SHIFTS + 2)] for n in range(num_nurses)) >= 4)  # P

        # Saturday
        model.Add(sum(shifts[(n, (w * 7 + 5) * NUM_SHIFTS)] for n in range(num_nurses)) == 2)  # N
        model.Add(sum(shifts[(n, (w * 7 + 5) * NUM_SHIFTS + 1)] for n in range(num_nurses)) == 2)  # A
        model.Add(sum(shifts[(n, (w * 7 + 5) * NUM_SHIFTS + 2)] for n in range(num_nurses)) == 2)  # P



    for n in range(num_nurses):
        for w in range(num_weeks):
            model.Add(sum(shifts[(n, w * 7 + ds)] for ds in range(7*NUM_SHIFTS)) == 5) #5days each week

    # A班后至少休1个班次，P休1，N休3
    for n in range(num_nurses):
        for ts in range(0, total_shifts - NUM_SHIFTS, NUM_SHIFTS):  # N班
            model.Add(sum([shifts[(n, ts + i)] for i in range(0, 4)]) <= 1)
        for ts in range(1, total_shifts, NUM_SHIFTS):  # A班
            model.Add(sum([shifts[(n, ts + i)] for i in range(0, 2)]) <= 1)
        for ts in range(2, total_shifts - NUM_SHIFTS, NUM_SHIFTS):  # P班
            model.Add(sum([shifts[(n, ts + i)] for i in range(0, 2)]) <= 1)

    max_work_nights = model.NewIntVar(0, num_days, 'max_work_nights')
    min_work_nights = model.NewIntVar(0, num_days, 'min_work_nights')

    work_nights = [sum(shifts[(n, d * NUM_SHIFTS)] for d in range(num_days)) for n in range(num_nurses)]

    model.AddMaxEquality(max_work_nights, work_nights)
    model.AddMinEquality(min_work_nights, work_nights)

    work_days = [sum(shifts[(n, ts)] for ts in range(total_shifts)) for n in range(num_nurses)]

    max_work_days = model.NewIntVar(0, num_days, 'max_work_days')
    min_work_days = model.NewIntVar(0, num_days, 'min_work_days')

    model.AddMaxEquality(max_work_days, work_days)
    model.AddMinEquality(min_work_days, work_days)

    # model.Minimize((max_work_nights - min_work_nights)*10 + (max_work_days - min_work_days) * 10  )
    model.Minimize((max_work_nights - min_work_nights) )

    # for n in range(num_nurses):
    #     for w in range(0, num_weeks):  # 每周
    #         model.Add(sum([shifts[(n, w * 7 * NUM_SHIFTS + ts)] for ts in range(0, 7 * NUM_SHIFTS)]) < 5)
            #         model.Add(sum([shifts[(n, w * 7 + d)] for d in range(0,7)]) >= 4)

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    solver.parameters.cp_model_presolve = False

    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        #schedule = [[[0 for _ in range(NUM_SHIFTS)] for _ in range(num_days)] for _ in range(num_nurses)]
        schedule = np.zeros((num_nurses, num_days))
        for d in range(num_days):
            for s in range(NUM_SHIFTS):
                for n in range(num_nurses):
                    if solver.BooleanValue(shifts[(n, d * NUM_SHIFTS + s)]):
                        schedule[n][d] = s + 1
        return schedule
    else:
        return None
