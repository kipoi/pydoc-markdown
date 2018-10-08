# Copyright (c) 2017  Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
This module implements preprocessing Markdown-like docstrings and converts
it to fully markdown compatible markup.
"""

import re


class Preprocessor(object):
    """
    This class implements the basic preprocessing.
     """

    def __init__(self, config):
        self.config = config

    def preprocess_section(self, section):
        """
        Preprocess the contents of *section*.
        """
        lines = []
        codeblock_opened = False
        current_section = None
        for line in section.content.split('\n'):
            if line.startswith("```"):
                codeblock_opened = (not codeblock_opened)
            if not codeblock_opened:
                line, current_section = self._preprocess_line(line, current_section)
            lines.append(line)
        section.content = self._preprocess_refs('\n'.join(lines))

    def _preprocess_line(self, line, current_section):
        match = re.match(r'# (.*)$', line)
        if match:
            current_section = match.group(1).strip().lower()
            line = re.sub(r'# (.*)$', r'__\1__\n', line)

        # TODO: Parse type names in parentheses after the argument/attribute name.
        if current_section in ('arguments', 'parameters'):
            style = r'- __\1__:\3'
        elif current_section in ('attributes', 'members', 'raises'):
            style = r'- `\1`:\3'
        elif current_section in ('returns',):
            style = r'`\1`:\3'
        else:
            style = None
        if style:
            #                  | ident  | types     | doc
            line = re.sub(r'\s*([^\\:]+)(\s*\(.+\))?:(.*)$', style, line)

        return line, current_section

    def _preprocess_refs(self, content):
        # TODO: Generate links to the referenced symbols.
        def handler(match):
            ref = match.group('ref')
            parens = match.group('parens') or ''
            has_trailing_dot = False
            if not parens and ref.endswith('.'):
                ref = ref[:-1]
                has_trailing_dot = True
            result = '`{}`'.format(ref + parens)
            if has_trailing_dot:
                result += '.'
            return (match.group('prefix') or '') + result
        return re.sub('(?P<prefix>^| |\t)#(?P<ref>[\w\d\._]+)(?P<parens>\(\))?', handler, content)


# --------------------------
# Custom Kipoi dataloader pre-processor
# by Ziga Avsec
from collections import OrderedDict

def section(title, content):
    return "**{title}**\n\n{content}".format(title=title, content=content)


def ul(l, level=0):
    return "\n".join(["    " * level + "- {}".format(x)for x in l])


def ul_dict(d, format_fn=lambda x: x, level=0):
    return ul(["**{k}**: {v}".format(k=k, v=format_fn(v)) for k, v in d.items()], level)


def ul_dict_nested(d, format_fn=lambda x: x, level=0):
    def optional_format(v):
        return "\n" + ul_dict_nested(v, format_fn, level + 1)

    if isinstance(d, OrderedDict):
        return ul(["**{k}**: {v}".format(k=k, v=optional_format(v)) for k, v in d.items()], level)
    elif isinstance(d, list):
        return ul([optional_format(v) for v in d], level)
    else:
        return ul([format_fn(d)], level)


def format_arg(v, level=0):
    from kipoi.specs import RemoteFile
    base = v.doc
    if isinstance(v.example, RemoteFile):
        base += " [example]({})".format(v.example.url)
    return base


def format_array_schema(schema):
    from kipoi.specs import MetadataStruct
    if isinstance(schema, MetadataStruct):
        if schema.name == "ranges":
            return "Genomic ranges: chr, start, end, name, strand"
        else:
            return schema.name
    else:
        return "**shape={}**, ".format(schema.shape) + schema.doc


def format_kipoi_dataloader(content):
    split_str = "```\n"
    code, descr_str = content.split(split_str)
    code += split_str

    # parse the other into Yaml
    from kipoi.data import DataLoaderDescription
    import related
    descr_str += "type: dummy\ndefined_as: dummy"
    descr = DataLoaderDescription.from_config(related.from_yaml(descr_str))
    out = code + "\n"
    out += descr.info.doc + "\n"
    out += "\n".join([
        section("Arguments", ul_dict(descr.args, format_arg)) + "\n",
        section("Output schema", ul_dict_nested(OrderedDict([
            ("inputs", descr.output_schema.inputs),
            ("targets", descr.output_schema.targets),
            ("metadata", descr.output_schema.metadata),
        ]), format_array_schema)),
    ])
    out += "\n"
    return out


# Custom DataLoader Yaml preprocessor
class DataLoaderYamlPreprocessor(Preprocessor):

    def preprocess_section(self, section):
        """
        Preprocess the contents of *section*.
        """
        if "output_schema:" in section.content and "args:" in section.content and "doc:" in section.content:
            section.content = format_kipoi_dataloader(section.content)
        else:
            # run the normal pre-processor
            super(DataLoaderYamlPreprocessor, self).preprocess_section(section)

