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
          [removeFree]
end function

rule removeFree
    replace [repeat declaration_or_statement]
        Head[declaration_or_statement]
        Tail[repeat declaration_or_statement]
    deconstruct Head 'free '( MA [macro_arguments] ') ';
    by
        Tail
end rule


