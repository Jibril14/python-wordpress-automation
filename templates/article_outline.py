# prompt_strings.py

STRING_ONE = 'I want you to be an expert in Food and Recipes and Generate an article outline for the topic "{main_keyword}".'

STRING_TWO = (
    'I want you to be an expert in food and culinary writing and Generate an article outline for the topic "{main_keyword}" '
    'and use the following articles as the primary source of reference: "{reference_links}"'
)

STRING_THREE = (
    'I want you to be an expert in food and culinary writing and Generate an article outline for the topic "{main_keyword}" '
    'and use the following articles as the primary source of reference: "{reference_links}". '
    'Make sure to discuss these in the article: "{secondary_keywords}"'
)

STRING_FOUR = (
    'I want you to be an expert in food and culinary writing and Generate an article outline for the topic "{main_keyword}", '
    'while making sure to discuss these in the article: "{secondary_keywords}"'
)

STRING_FIVE = (
    "Give me strictly just the outline as output, there should be Introduction heading at the start followed by the individual headings for the content. "
    "No need for Conclusion. Use H2 style headings for each entry, and there should be no subheadings. "
    "Make the headings engaging, but keep it under 50 characters. Do not give me any additional text other than the outline. "
    "Make sure the output is in JSON so that it's easier to access the headings.\n"
    'Here\'s the JSON structure I want to use.'
)
