using JuMP, MadNLP
using JSON


println("CHILD START!")
flush(stdout)

for line in eachline(stdin)
    println("CHILD $(uppercase(line))")
    flush(stdout)
    
    if strip(line) == "quit"
        break
    end
end

exit(0)
