include "c.Grm"
include "REDAWN.Txl"

function main
    replace [program]
        P [program]
    by
        P [MutationDriver]
end function

function MutationDriver
    replace [program]
        P [program]
    by
        P [preparationTransformations]
end function

function preparationTransformations
    replace [program]
        P [program]
    by
        P [REDAWN]
end function
