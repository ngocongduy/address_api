from .address_comparison import address_comparison
from . decimalencoder import DecimalEncoder
comparer = address_comparison.AddressComparer()

import json
def remove_some_value(compare_result):
    key_to_remove = {'count','type','addr1_pos','addr2_pos'}
    if type(compare_result) is dict:
        for k in key_to_remove:
            try:
                compare_result.pop(k)
            except:
                pass
    return compare_result
def lambda_handler(event, context):
    print(event)
    body = json.loads(event.get("body"))
    addr1 = body.get('addr1')
    addr2 = body.get('addr2')

    result = comparer.fuzzy_compare(addr1,addr2)
    if result is None:
        result = {"error":"Result is None"}
    else:
        result = remove_some_value(result)

    response = {
        "statusCode": 200,
        "body": json.dumps(result, cls=DecimalEncoder)
    }
    return response