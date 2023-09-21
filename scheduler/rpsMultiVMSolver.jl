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
    myMin(x) = (min(x, 1))
    model_disc = Model(() -> MadNLP.Optimizer())
    register(model_disc, :myMin, 1, myMin, autodiff=true)
    set_silent(model_disc)
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
                    abs((myMin(y[i, j])) - matrix_prev_offloadings[i][j]) for j in 1:n_hosts
                )
            ) for i in 1:n_funcs
        )
    )
    @NLobjective(
        model_disc, Min, cost_func
    )
    
    optimize!(model_disc)
    
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
    myMin(x) = (min(x, 1))
    
    model_disc = Model(() -> MadNLP.Optimizer())
    register(model_disc, :myMin, 1, myMin, autodiff=true)
    set_silent(model_disc)
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
                        
                        myMin(y[x["tmpIndex"][1], x["tmpIndex"][2]]) * 
                        x["coeff"]
                        for x in exp1
                    
                    )
                    +
                    sum(
                    
                        (
                            (
                                myMin(y[x["tmpIndex1"][1], x["tmpIndex1"][2]]) *
                                myMin(y[x["tmpIndex2"][1], x["tmpIndex2"][2]]) *
                                x["coeff1"]
                            ) 
                            +
                            (
                                (1 - myMin(y[x["tmpIndex1"][1], x["tmpIndex1"][2]])) *
                                myMin(y[x["tmpIndex2"][1], x["tmpIndex2"][2]]) *
                                x["coeff2"]
                            ) 
                            + 
                            (
                                myMin(y[x["tmpIndex1"][1], x["tmpIndex1"][2]]) *
                                (1 - myMin(y[x["tmpIndex2"][1], x["tmpIndex2"][2]])) *
                                x["coeff3"]
                            )
                        ) for x in exp2
                    
                    )
                     +
                    (
                        myMin(y[(exp3["tmpIndex"])[1], (exp3["tmpIndex"])[2]]) * exp3["coeff"]
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
                    abs(myMin(y[i, j]) - matrix_prev_offloadings[i][j]) for j in 1:n_hosts
                )
            ) for i in 1:n_funcs
        )
    )
    @NLobjective(
        model_disc, Min, cost_func
    )
    optimize!(model_disc)
    
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
    # solution = [[float(x_i) for x_i in x] for x in json_parsed["solution"]]
    expression_1 = json_parsed["expression_1"]
    expression_2 = json_parsed["expression_2"]
    expression_3 = json_parsed["expression_3"]
    inequality_const = inequality_const = [float(c) for c in json_parsed["inequality_const"]]
    expression_1 = [
        [
            [
                Dict([
                    ("tmpIndex", [1+Int(x_i["tmpIndex"][1]), 1+Int(x_i["tmpIndex"][2])]),
                    ("coeff", float(x_i["coeff"])),

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

    sol = [[(round(abs(s_i), digits=2)) for s_i in s] for s in sol]
    sol = [[s_i >= 1 ? s_i : 0 for s_i in s] for s in sol]
    
    return sol
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
    # solution = [[float(x_i) for x_i in x] for x in json_parsed["solution"]]
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
    sol = [[(round(abs(s_i), digits=2)) for s_i in s] for s in sol]
    sol = [[s_i >= 1 ? s_i : 0 for s_i in s] for s in sol]
    
    return sol
end

function warmup()
    model = Model(()->MadNLP.Optimizer(print_level=MadNLP.INFO, max_iter=100))
    set_silent(model)
    @variable(model, x, start = 0.0)
    @constraint(model, x <= 1)
    @variable(model, y, start = 0.0)
    @constraint(model, y <= 1)
    @NLobjective(model, Max, x+y)
    optimize!(model)
end



function main()
    warmup()
    
    # println("Julia Started!")
    # flush(stdout)

    while true        
        f_in = open("./scheduler/juliaStdin", "r")
        for line in eachline(f_in)
            if cmp(line, "END") == 0
                return
            end

            json_parsed = JSON.parse(line, inttype=Int64)
            mode = json_parsed["mode"] 
            
            sol = "None"
            
            if cmp(mode, "latency") == 0
                sol = call_latency(json_parsed)
            else
                sol = call_cost(json_parsed)
            end

            f_out = open("./scheduler/juliaStdout", "w")
            JSON.print(f_out, sol)
            flush(f_out)
            close(f_out)
        end

        close(f_in)
    end
end



main();