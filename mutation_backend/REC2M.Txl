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
          [replace_calloc_W_malloc]
          [replace_xcalloc_W_xmalloc]
end function


rule replace_calloc_W_alloca 
	replace $ [assignment_expression]
		A[any]'calloc '( AE1 [assignment_expression],AE2 [assignment_expression] ')
	construct E1 [expression] AE1
	construct E2 [expression] AE2
	by
		A'alloca '('(E1') * '(E2') ')
end rule

rule replace_xcalloc_W_alloca
	replace $ [assignment_expression]
		A[any]'xcalloc '( AE1 [assignment_expression],AE2 [assignment_expression] ')
	construct E1 [expression] AE1
	construct E2 [expression] AE2
	by
		A'alloca '('(E1') * '(E2') ')
end rule 

