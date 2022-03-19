# -*- coding: utf-8 -*-
"""
19 Mar 22

cookieFormatter()


"""

def cookieFormatter():
    '''
    cookieFormatter prompts the user to paste web-browsing cookies into the
    console. It returns the cookies in the form a  dictionary.
    
    The input must be copied from the developer tools window in a web browser.
    Cookies can be found by navigating to the network tab. Then, selecting the
        

    Returns
    -------
    cookie_dict : dictionary
        A dictionary where keys are cookie names and values are cookie values
    '''
    raw_dough = input("Please paste cookies:\n\n")
    
    print("\nThank you.\n\n")
    
    split_dough = raw_dough.split("; ")
    
    key_value_pairs = [x.split("=") for x in split_dough]
    
    cookies = dict(key_value_pairs)
    
    return cookies