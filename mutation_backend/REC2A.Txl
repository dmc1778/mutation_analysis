include "CL.Grm"

function main
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
          [replace_malloc_W_alloca]
          [replace_xmalloc_W_alloca]
end function


rule replace_malloc_W_alloca
	replace $[assignment_expression]
		A[any]'malloc '( AL [list argument_expression] ')
	by
		A'alloca '( AL ')
end rule

rule replace_xmalloc_W_alloca
	replace $[assignment_expression]
		A[any]'xmalloc '( AL [list argument_expression] ')
	by
		A'alloca '( AL ')
end rule

