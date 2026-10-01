## Khuyến nghị mô hình

| model     | label                        |   n_pass_var99 |   crisis_UR_VaR99 |   complexity |   overall_rank | verdict                            |
|:----------|:-----------------------------|---------------:|------------------:|-------------:|---------------:|:-----------------------------------|
| HS        | Mô phỏng lịch sử (HS)        |              0 |             5,565 |            1 |              1 | Chưa được hai kiểm định VaR ủng hộ |
| GARCH_N   | GARCH(1,1) (GARCH_N)         |              0 |             5,464 |            3 |              2 | Chưa được hai kiểm định VaR ủng hộ |
| MC_Normal | Monte Carlo (MC_Normal)      |              0 |             9,019 |            2 |              3 | Chưa được hai kiểm định VaR ủng hộ |
| Normal    | Phương pháp tham số (Normal) |              0 |             9,047 |            1 |              4 | Chưa được hai kiểm định VaR ủng hộ |
