.text
main:
    addi $t0, $zero, 5       # $t0 = 5
    addi $t1, $zero, 10      # $t1 = 10

    add  $t2, $t0, $t1       # $t2 = 15 (data hazard from t0 and t1)
    sub  $t3, $t2, $t0       # $t3 = 10 (hazard from t2)
    add  $t4, $t3, $t1       # $t4 = 20 (hazard from t3)

    lw   $t5, 0($t2)         # load from memory at address in t2 (t2=15)
    add  $t6, $t5, $t0       # hazard from load (load-use hazard)

    sw   $t6, 4($t2)         # store result to memory (address 19)

    beq  $t0, $t0, branch_taken  # always taken

    addi $t7, $zero, 99      # should be skipped
branch_taken:
    addi $t7, $zero, 42      # branch target
