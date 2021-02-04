function REDAWN
    replace [program]
        P [program]
    by
        P [malloc_replace]
end function

function malloc_replace
    replace [program]
        P [program]
    by
        P 
          [replace_malloc_W_N]
          [replace_xmalloc_W_N]
end function


rule replace_malloc_W_N
    replace $ [assignment_expression]
        A[any]'malloc '( AE [list argument_expression] ')
    by
        'NULL
end rule

rule replace_xmalloc_W_N
    replace $ [assignment_expression]
        A[any]'xmalloc '( AE [list argument_expression] ')
    by
        'NULL
end rule

