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
          [replace_malloc_size_W_zero]
          [replace_xmalloc_size_W_zero]
end function

rule replace_malloc_size_W_zero
	replace $[assignment_expression]
		A[any]'malloc '( AL [list argument_expression] ')
	by
		A'malloc '( 0 ')
end rule

rule replace_xmalloc_size_W_zero
	replace $[assignment_expression]
		A[any]'xmalloc '( AL [list argument_expression] ')
	by
		A'xmalloc '( 0 ')
end rule


