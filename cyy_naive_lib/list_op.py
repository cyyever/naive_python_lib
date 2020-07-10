def split_list_to_chunks(my_list: list, chunk_size: int):
    return [my_list[offs: offs + chunk_size]
            for offs in range(0, len(my_list), chunk_size)]


def dict_values_to_list(d: dict):
    r"""
    Construct a list containing the dictionary values by key order.
    """
    res = []
    for k in sorted(d.keys()):
        res.append(d[k])
    return res
