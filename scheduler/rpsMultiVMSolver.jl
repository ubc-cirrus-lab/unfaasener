using JuMP, MadNLP
using JSON

function solve_cost(
    n_hosts,
    n_funcs,
    locality,
    list_mem_capacity,
    list_cpu_capacity,
    list_func_costs_1,
    list_func_costs_2,
    matrix_cpu_coeff,
    matrix_mem_coeff,
    matrix_prev_offloadings
)
    model_disc = Model(() -> MadNLP.Optimizer())
    set_silent(model_disc)
    set_optimizer_attribute(model_disc, "LogLevel", "Error")
    @variable(model_disc, 0 <= y[1:n_funcs, 1:n_hosts] <= 100)
    for i in 1:n_funcs
        @constraint(
            model_disc,
            sum(
                [y[i, j] for j in 1:n_hosts]
            ) <= 100
        )
    end
    for j in 1:n_hosts
        @constraint(
            model_disc,
            sum(
                [
                    y[i, j]*matrix_cpu_coeff[i][j]/100 for i in 2:n_funcs
                ]
            ) <= list_cpu_capacity[j]
        )
        @constraint(
            model_disc,
            sum(
                [
                    y[i, j]*matrix_mem_coeff[i][j]/100 for i in 2:n_funcs
                ]
            ) <= list_mem_capacity[j]
        )
        @constraint(
            model_disc,
            y[1, j] == 0
        )
    end
    @NLexpression(
        model_disc, cost_func, 
        sum(
            (
                list_func_costs_1[i]*(1 - sum((y[i, j]) for j in 1:n_hosts)/100) +
                list_func_costs_2[i]*(sum((y[i, j]) for j in 1:n_hosts)/100) +
                (10^3)*locality*sum(
                    abs(min(y[i, j], 1) - matrix_prev_offloadings[i][j]) for j in 1:n_hosts
                )
            ) for i in 1:n_funcs
        )
    )
    @NLobjective(
        model_disc, Min, cost_func
    )
    optimize!(model_disc)
    # for i in 1:n_funcs
    #     for j in 1:n_hosts
    #         println("offloading $i on $j = $(value(y[i, j]))")
    #     end
    # end
    result = [[value(y[i, j]) for j in 1:n_hosts] for i in 1:n_funcs]
    return result
end


function solve_latency(
    n_hosts,
    n_funcs,
    locality,
    list_mem_capacity,
    list_cpu_capacity,
    list_func_costs_1,
    list_func_costs_2,
    expression_1,
    expression_2,
    expression_3,
    inequality_const,
    matrix_cpu_coeff,
    matrix_mem_coeff,
    matrix_prev_offloadings
)
    model_disc = Model(() -> MadNLP.Optimizer())
    set_silent(model_disc)
    set_optimizer_attribute(model_disc, "LogLevel", "Error")
    @variable(model_disc, 0 <= y[1:n_funcs, 1:n_hosts] <= 100)
    for i in 1:n_funcs
        @constraint(
            model_disc,
            sum(
                [y[i, j] for j in 1:n_hosts]
            ) <= 100
        )
    end
    for j in 1:n_hosts
        @constraint(
            model_disc,
            sum(
                [
                    y[i, j]*matrix_cpu_coeff[i][j]/100 for i in 2:n_funcs
                ]
            ) <= list_cpu_capacity[j]
        )
        @constraint(
            model_disc,
            sum(
                [
                    y[i, j]*matrix_mem_coeff[i][j]/100 for i in 2:n_funcs
                ]
            ) <= list_mem_capacity[j]
        )
        @constraint(
            model_disc,
            y[1, j] == 0
        )
    end


    for i_dur in 1:size(expression_1)[1]
        for i_c in 1:size(expression_1[1])[1]
            exp1 = expression_1[i_dur][i_c]
            exp2 = expression_2[i_dur][i_c]
            exp3 = expression_3[i_dur][i_c]
            ineq_c = inequality_const[i_dur]

            @NLconstraint(
                model_disc,
                (    
                    sum(
                        
                        min(y[x["tmpIndex"][1], x["tmpIndex"][2]], 1) * x["coeff"]
                        for x in exp1
                    
                    )
                    +
                    sum(
                    
                        (
                            (
                                min(y[x["tmpIndex1"][1], x["tmpIndex1"][2]], 1) *
                                min(y[x["tmpIndex2"][1], x["tmpIndex2"][2]], 1) *
                                x["coeff1"]
                            ) +
                            (
                                (1 - min(y[x["tmpIndex1"][1], x["tmpIndex1"][2]], 1)) *
                                min(y[x["tmpIndex2"][1], x["tmpIndex2"][2]], 1) *
                                x["coeff2"]
                            ) + 
                            (
                                min(y[x["tmpIndex1"][1], x["tmpIndex1"][2]], 1) *
                                (1 - min(y[x["tmpIndex2"][1], x["tmpIndex2"][2]], 1)) *
                                x["coeff3"]
                            )
                        ) for x in exp2
                    
                    )
                    +
                    (
                        min(y[(exp3["tmpIndex"])[1], (exp3["tmpIndex"])[2]], 1) * exp3["coeff"]
                    )
                ) <= ineq_c
            )


        end
    end




    @NLexpression(
        model_disc, cost_func, 
        sum(
            (
                list_func_costs_1[i]*(1 - sum((y[i, j]) for j in 1:n_hosts)/100) +
                list_func_costs_2[i]*(sum((y[i, j]) for j in 1:n_hosts)/100) +
                (10^3)*locality*sum(
                    abs(min(y[i, j], 1) - matrix_prev_offloadings[i][j]) for j in 1:n_hosts
                )
            ) for i in 1:n_funcs
        )
    )
    @NLobjective(
        model_disc, Min, cost_func
    )
    optimize!(model_disc)
    # for i in 1:n_funcs
    #     for j in 1:n_hosts
    #         println("offloading $i on $j = $(value(y[i, j]))")
    #     end
    # end
    # println(model_disc)
    result = [[value(y[i, j]) for j in 1:n_hosts] for i in 1:n_funcs]
    return result
end



function call_latency(json_parsed)
    n_hosts = Int(json_parsed["n_hosts"])
    n_funcs = Int(json_parsed["n_funcs"])
    locality = float(json_parsed["locality"])
    matrix_prev_offloadings = [[float(x_i) for x_i in x] for x in json_parsed["matrix_prev_offloadings"]]
    matrix_mem_coeff = [[float(x_i) for x_i in x] for x in json_parsed["matrix_mem_coeff"]]
    matrix_cpu_coeff = [[float(x_i) for x_i in x] for x in json_parsed["matrix_cpu_coeff"]]
    list_cpu_capacity = [float(x) for x in json_parsed["list_cpu_capacity"]]
    list_mem_capacity = [float(x) for x in json_parsed["list_mem_capacity"]]
    list_func_costs_1 = [float(x) for x in json_parsed["list_func_costs_1"]]
    list_func_costs_2 = [float(x) for x in json_parsed["list_func_costs_2"]]
    solution = [[float(x_i) for x_i in x] for x in json_parsed["solution"]]
    expression_1 = json_parsed["expression_1"]
    expression_2 = json_parsed["expression_2"]
    expression_3 = json_parsed["expression_3"]
    inequality_const = inequality_const = [float(c) for c in json_parsed["inequality_const"]]
    expression_1 = [
        [
            [
                Dict([
                    ("tmpIndex", [1+Int(x_i["tmpIndex"][1]), 1+Int(x_i["tmpIndex"][2])]),
                    ("coeff", Int(x_i["coeff"])),

                ]) for x_i in x
            ] for x in X
        ] for X in expression_1
    ];

    expression_2 = [
        [
            [
                Dict([
                    ("tmpIndex1", [1+Int(x_i["tmpIndex1"][1]), 1+Int(x_i["tmpIndex1"][2])]),
                    ("tmpIndex2", [1+Int(x_i["tmpIndex2"][1]), 1+Int(x_i["tmpIndex2"][2])]),
                    ("coeff1", float(x_i["coeff1"])),
                    ("coeff2", float(x_i["coeff2"])),
                    ("coeff3", float(x_i["coeff3"]))
                ]) for x_i in x
            ] for x in X
        ] for X in expression_2
    ];

    expression_3 = [
        [
            Dict([
                ("tmpIndex", [1+Int(x["tmpIndex"][1]), 1+Int(x["tmpIndex"][2])]),
                ("coeff", float(x["coeff"])),
            ])
            for x in X
        ] for X in expression_3
    ]
        
    sol = solve_latency(
        n_hosts,
        n_funcs,
        locality,
        list_mem_capacity,
        list_cpu_capacity,
        list_func_costs_1,
        list_func_costs_2,
        expression_1,
        expression_2,
        expression_3,
        inequality_const,
        matrix_cpu_coeff,
        matrix_mem_coeff,
        matrix_prev_offloadings
    )

    sol = [[round(s_i) for s_i in s] for s in sol]

    open("solver_output.json", "w") do f
        JSON.print(f, sol)
    end
end

function call_cost(json_parsed)
    n_hosts = Int(json_parsed["n_hosts"])
    n_funcs = Int(json_parsed["n_funcs"])
    locality = float(json_parsed["locality"])
    matrix_prev_offloadings = [[float(x_i) for x_i in x] for x in json_parsed["matrix_prev_offloadings"]]
    matrix_mem_coeff = [[float(x_i) for x_i in x] for x in json_parsed["matrix_mem_coeff"]]
    matrix_cpu_coeff = [[float(x_i) for x_i in x] for x in json_parsed["matrix_cpu_coeff"]]
    list_cpu_capacity = [float(x) for x in json_parsed["list_cpu_capacity"]]
    list_mem_capacity = [float(x) for x in json_parsed["list_mem_capacity"]]
    list_func_costs_1 = [float(x) for x in json_parsed["list_func_costs_1"]]
    list_func_costs_2 = [float(x) for x in json_parsed["list_func_costs_2"]]
    solution = [[float(x_i) for x_i in x] for x in json_parsed["solution"]]
    sol = solve_cost(
        n_hosts,
        n_funcs,
        locality,
        list_mem_capacity,
        list_cpu_capacity,
        list_func_costs_1,
        list_func_costs_2,
        matrix_cpu_coeff,
        matrix_mem_coeff,
        matrix_prev_offloadings
    );
    sol = [[round(s_i) for s_i in s] for s in sol]
    open("solver_output.json", "w") do f
        JSON.print(f, sol)
    end
end



function main()
    json_parsed = JSON.parsefile("solver_input.json", inttype=Int64)
    mode = json_parsed["mode"] 
    if cmp(mode, "latency") == 0
        call_latency(json_parsed)
    else
        call_cost(json_parsed)
    end
end



main();