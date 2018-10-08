content = """
```python
SeqStringDataset(self, intervals_file, fasta_file, num_chr_fasta=False, label_dtype=None, auto_resize_len=None, use_strand=False, force_upper=True)
```

info:
    doc: >
       Dataloader for a combination of fasta and tab-delimited input files such as bed files. The dataloader extracts
       regions from the fasta file as defined in the tab-delimited `intervals_file`. Returned sequences are of the type
       np.array([str]).
args:
    intervals_file:
        doc: bed3+<columns> file path containing intervals + (optionally) labels
        example:
          url: https://raw.githubusercontent.com/kipoi/kipoiseq/kipoi_dataloader/tests/data/sample_intervals.bed
          md5: ecc4cf3885318a108adcc1e491463d36
    fasta_file:
        doc: Reference genome FASTA file path.
        example:
          url: https://raw.githubusercontent.com/kipoi/kipoiseq/kipoi_dataloader/tests/data/sample.5kb.fa
          md5: 6cefc8f443877490ab7bcb66b0872e30
    num_chr_fasta:
        doc: True, the the dataloader will make sure that the chromosomes don't start with chr.
    label_dtype:
        doc: None, datatype of the task labels taken from the intervals_file. Allowed - string', 'int', 'float', 'bool'
    auto_resize_len:
        doc: None, required sequence length.
    # max_seq_len:
    #     doc: maximum allowed sequence length
    use_strand:
        doc: reverse-complement fasta sequence if bed file defines negative strand
    force_upper:
        doc: Force uppercase output of sequences
output_schema:
    inputs:
        name: seq
        shape: ()
        doc: DNA sequence as string
        special_type: DNAStringSeq
        associated_metadata: ranges
    targets:
        shape: (None,)
        doc: (optional) values following the bed-entry - chr  start  end  target1   target2 ....
    metadata:
        ranges:
            type: GenomicRanges
            doc: Ranges describing inputs.seq
"""


from collections import OrderedDict


def section(title, content, level=3):
    return "#" * level + " {title}\n\n{content}".format(title=title, content=content)


def ul(l, level=0):
    return "\n".join(["    " * level + "- {}".format(x)for x in l])


def ul_dict(d, format_fn=lambda x: x, level=0):
    return ul(["***{k}***: {v}".format(k=k, v=format_fn(v)) for k, v in d.items()], level)


def ul_dict_nested(d, format_fn=lambda x: x, level=0):
    def optional_format(v):
        return "\n" + ul_dict_nested(v, format_fn, level + 1)

    if isinstance(d, OrderedDict):
        return ul(["***{k}***: {v}".format(k=k, v=optional_format(v)) for k, v in d.items()], level)
    elif isinstance(d, list):
        return ul([optional_format(v) for v in d], level)
    else:
        return ul([format_fn(d)], level)


from kipoi.specs import RemoteFile
from kipoi.specs import MetadataStruct


def format_arg(v, level=0):
    base = v.doc
    if isinstance(v.example, RemoteFile):
        base += " [example]({})".format(v.example.url)
    return base


def format_array_schema(schema):
    if isinstance(schema, MetadataStruct):
        if schema.name == "ranges":
            return "Genomic ranges: chr, start, end, name, strand"
        else:
            return schema.name
    else:
        return "***shape={}***, ".format(schema.shape) + schema.doc


def split_python(content):

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
        section("Arguments", ul_dict(descr.args, format_arg)),
        section("Output schema", ul_dict_nested(OrderedDict([
            ("inputs", descr.output_schema.inputs),
            ("targets", descr.output_schema.targets),
            ("metadata", descr.output_schema.metadata),
        ]), format_array_schema)),
    ])
    return out


def test_split():
    print(split_python(content))
