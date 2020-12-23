from django.core.management import call_command
import re
from unidecode import unidecode


# run elastic search command to rebuild index
def rebuild_elasticsearch_index():
    call_command('search_index', '--rebuild', '-f')


# run elastic search command to delete index
def delete_elasticsearch_index():
    call_command('search_index', '--delete', '-f')


def is_not_empty_or_null(value):
    if value is None:
        return False
    else:
        if type(value) is str:
            if len(value) > 0:
                return True
        elif type(value) is int:
            return True
        return False


def clean_alphanumeric_slash(value: str):
    result = unidecode(value).lower()
    return re.sub(r"[^a-z0-9/]", '', result)


def clean_remove_accent_lower(value: str):
    result = unidecode(value).lower()
    return result


def clean_and_split_into_parts_for_formatted_address(value: str):
    result = {}
    order = ('street', 'ward', 'district', 'province')
    if len(value) > 0:
        # addr = clean_remove_accent_lower(value)
        addr = value.lower()
        words = addr.split(',')
        for i in range(len(words)):
            value = words[i]
            for e in order:
                if e in value:
                    value = value.replace(e, '')

            value = value.strip()
            if len(value) > 0:
                words[i] = value
            else:
                words[i] = None

        if 'vietnam' in words[-1]:
            words[-1] = None
        # Remove None
        parts = [e for e in words if e]
        length = len(parts)
        if length > 4:
            boundary = length - 3
            all_head_in_one = ' '.join(parts[0:boundary])
            parts = [all_head_in_one] + parts[boundary:]
        if len(parts) == 4:
            # pass
            result = ', '.join(parts)
        else:
            result = ' '.join(parts)
        # else:
        #     prefix = []
        #     temp = parts.copy()
        #     while not len(temp) >= 4:
        #         prefix.append('')
        #         temp.append('')
        #     parts = prefix + parts
        # for i in range(len(order)):
        #     result[order[i]] = parts[i]
    return result


def clean_alphanumeric_space(address: str):
    def _only_alphanumeric_space(address: str):
        return re.sub(r'[^A-Za-z0-9\s]', '', address)

    def _comma_dot_to_space(address: str):
        return re.sub(r'[,.]', ' ', address)

    try:
        result = unidecode(address)
        result = _comma_dot_to_space(result)
        return _only_alphanumeric_space(result).lower()
    except Exception as e:
        print(e)
        return address


def clean_and_split_into_words_sorted(addr: str):
    result = []
    if len(addr) > 0:
        addr = clean_alphanumeric_space(addr)
        words = addr.split()
        words = set(words)
        for w in sorted(words):
            result.append(w)
    return result
