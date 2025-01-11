# Transactions analyzing
**views**
- *main_page* - gets date and returns json with key:
    - greeting - gets data from the greeting function.
    - cards - gets data from the get_cards_info function.
    - top_transactions -get data from the get_top_transactions function.
    - currency_rates - gets data from the get_user_prefer_rates function.
    - stock_prices - gets data from the get_user_stocks function.
- *greeting* - greeting by time (good day/morning/evening/night) 
- *get_cards_info* - returns list of card numbers and the amount spent for 
the month of the date.
- *get_top_transaction* - returns top 5 transactions for the month of 
the specified data.
- *get_user_prefer_currency_rates* - returns currency rates enums in 
the user_setting file for the current day. 
- *get_user_stocks* - returns stock prices of S&P500 for the current day.

**test_views**
- *test_greeting* - the test to verify the correctness the greeting 
function execution depending on the current time.
- *test_get_cards_info* - the test the correctness of the get_cards_info 
response.
- *test_get_cards_info_error* - the test the correctness of 
the get_cards_info which got a bad excel currency symbol.
- *test_get_top_transactions* - the test getting top 5 transaction list.
- *test_get_top_transactions_empty* - testing get_top_transactions getting 
empty list
- *test_get_user_prefer_currency_rates* - the test for 
the get_user_prefer_currency_rates function.
- *test_get_user_stocks* - the test for the get_user_stocks function.
- *test_get_bad_url_user_stocks* - the test for the get_user_stocks got 
bad api key.
- *test_get_bad_user_stocks* - the test for the get_user_stocks got 
bad json data.
- *test_main_page* - the for the main_page function.
- *test_main_page_no_user_settings* - the test for the main_page got 
a not exist user settings Json file.

**utils**
- *read_excel* - get Pandas DataFrame data from Excel file.
- *get_user_settings* - get user settings from a Json file.
- *get_date* - convert date from str to datetime.date.
- *exchange* - exchange the currency to ruble ('RUB').
- *get_currency_rates* - the decorator for for specified get currency 
rates API.
- *get_currency_rates_by_cbr* - get currency rates from CBR 
(Central Bank of RF) API in XML format.
- *mask_card* - get last 4 digits from bank card number.

**test_utils**
- *test_read_excel* - the test to verify the correctness 
the read_excel function.
- *test_not_exist_excel* - the test for the read_excel function got 
not exist excel file.
- *test_get_user_settings* - the test for get_useer_settings got not exist 
user settings Json file.
- *test_get_date* - testing convert date from str to datetime.date.
- *test_exchange* - the test to verify the correctness 
the exchange function.
- *test_get_currency_rates* - the test to verify the correctness 
the decorator.
- *test_get_currency_rates_by_cbr* - the test to verify the correctness 
the get_currency_rates_by_cbr function. 
- *test_bad_xml_data* - the test for the get_currency_rates_by_cbr 
function got bad XML data.
- *test_bad_xml_rate* - the test for the get_currency_rates_by_cbr 
function got bad XML data for currency rate.
- *test_mask_card* - the test to verify the correctness 
the mask_card function.

**services**
- *search_individual_transfers* - gets transactions for transfers to 
individuals by JSON format.

**test_services**
- *test_search_individual_transfers* - the test to verify the correctness 
the search_individual_transfers function. 
- *test_search_individual_transfers_empty_data* - the test for 
the search_individual_transfers got empty Excel data.
- *test_search_individual_transfers_empty_filtered* - the test for 
the search_individual_transfers got empty transaction data after filtering.
- *test_search_individual_transfers_key_error* - the test for 
the search_individual_transfers got transaction data with bad key.

**reports**
- *write_report* - the decorator for writing report data to Json file.
- *spending_by_category* - generate report of spending by category for 
3 months

**test_reports**
- *test_spending_by_category* - the test to verify the correctness 
the spending_by_category function.
- *test_spending_by_category_bad_filename* - testing writing a report on 
an incorrect path to a json file.
- *test_spending_by_category_bad_dataframe* - the test for 
the spending_by_category function got bad excel data.
