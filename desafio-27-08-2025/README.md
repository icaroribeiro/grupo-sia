            - Add a new column named `daily_meal_voucher_value` to `df1` DataFrame. This column should simply contain the daily value of the meal voucher.
                - Logic: The value in this column will be the same as the value in the existing `meal_voucher_value` column.
            - Add a new column named `total_meal_voucher_value` to `df1` DataFrame. This column will calculate the total benefit amount to be granted for the month.
                - Formula: `total_meal_voucher_value` = `effective_working_days` * `daily_meal_voucher_value`
            - Add a new column named `company_meal_voucher_cost` to `df1` DataFrame. This column will represent the company's share of the meal voucher cost (80%).
                - Formula: `company_meal_voucher_cost` = `total_meal_voucher_value` * 0.80
            - Add a new column named `employee_meal_voucher_discount` to `df1` DataFrame. This column will represent the portion to be discounted from the employee (20%).
                - Formula: `employee_meal_voucher_discount` = `total_meal_voucher_value` * 0.20



    			                5. `daily_meal_voucher_value`
                6. `total_meal_voucher_value`
                7. `company_meal_voucher_cost`
                8. `employee_meal_voucher_discount`


    			            - Rename the `daily_meal_voucher_value` column of the `resulting` DataFrame to `VALOR DIÁRIO VR`.
            - Rename the `total_meal_voucher_value` column of the `resulting` DataFrame to `TOTAL`.
            - Rename the `company_meal_voucher_cost` column of the `resulting` DataFrame to `Custo empresa`.
            - Rename the `employee_meal_voucher_discount` column of the `resulting` DataFrame to `Desconto profissional`.
            - Add a new column named `Competência` and fill out the rows with value `01/05/2025`.


                6. `VALOR DIÁRIO VR`
                7. `TOTAL`
                8. `Custo empresa`
                9. `Desconto profissional`
