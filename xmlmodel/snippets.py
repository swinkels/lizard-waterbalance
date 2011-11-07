#!/usr/bin/python


def parse_parameters(stream):
    r"""parse the xml stream into set of objects

    create as many objects as the `group` elements in the input file.

    each `group` element causes an object needs a `model` element, which
    names the class of the resulting object.

    ====
    the first object in the stream is considered the root of the
    resulting structure.

    >>> from nens.mock import Stream
    >>> type(parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model></group>
    ... </parameters>''')))
    <class 'xmlmodel.snippets.Area'>

    ====
    each `parameter` in the `group` cause a field in the resulting
    object, the name of the field is in the `id` attribute of the
    `parameter`, according to whether the `parameter` contains a
    `boolValue`, `dblValue` or a `stringValue`, the field will be a
    boolean, a double or a string, respectively.  the text in the
    element specifies the value of the field.

    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id="ts_refcl1">
    ... <boolValue>false</boolValue>
    ... </parameter>
    ... </group></parameters>'''))
    >>> root.ts_refcl1
    False

    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id="max_inl">
    ... <dblValue>144000</dblValue>
    ... </parameter>
    ... </group></parameters>'''))
    >>> root.max_inl
    144000.0

    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id="geb_naam">
    ... <stringValue>Aetsveldsche polder oost</stringValue>
    ... </parameter>
    ... </group></parameters>'''))
    >>> root.geb_naam
    'Aetsveldsche polder oost'

    ====
    all subsequent objects will be associated to the root, in a field
    named as the class of the object.

    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... </group><group>
    ... <model>Bucket</model>
    ... </group><group>
    ... <model>Bucket</model>
    ... </group><group>
    ... <model>Pump</model>
    ... </group></parameters>'''))
    >>> len(root.bucket)
    2
    >>> len(root.pump)
    1
    >>> type(root)
    <class 'xmlmodel.snippets.Area'>
    >>> set([type(i) for i in root.bucket])
    set([<class 'xmlmodel.snippets.Bucket'>])
    >>> set([type(i) for i in root.pump])
    set([<class 'xmlmodel.snippets.Pump'>])

    """

    classes = {}

    from xml.dom.minidom import parse
    d = parse(stream)
    rootNode = d.childNodes[0]
    groupNodes = [i for i in rootNode.childNodes if i.nodeType != i.TEXT_NODE]

    result = None

    for group in groupNodes:
        models = group.getElementsByTagName("model")
        assert(len(models) == 1)
        for model in models:
            class_name = str(model.childNodes[0].nodeValue)
            this_class = classes.setdefault(class_name, type(class_name, (object, ), {}))

        obj = this_class()
        if result is None:
            result = obj
        for parameter in group.getElementsByTagName("parameter"):
            try:
                value_node = parameter.getElementsByTagName("dblValue")[0]
                value = float(value_node.childNodes[0].nodeValue)
            except IndexError:
                try:
                    value_node = parameter.getElementsByTagName("stringValue")[0]
                    value = str(value_node.childNodes[0].nodeValue)
                except IndexError:
                    try:
                        value_node = parameter.getElementsByTagName("boolValue")[0]
                        value = (value_node.childNodes[0].nodeValue).lower().strip() == "true"
                    except IndexError:
                        value = None
            setattr(obj, parameter.getAttribute('id'), value)

        if obj != result:
            if not hasattr(result, class_name.lower()):
                setattr(result, class_name.lower(), [])
            getattr(result, class_name.lower()).append(obj)

    return result


def attach_timeseries_to_structures(root, tsd, corresponding):
    """couple objects to the corresponding time series.

    root is an object as returned by parse_parameters.

    tsd is a dictionary as returned by timeseries.TimeSeries.as_dict.

    corresponding is a dictionary associating a class name to a
    dictionary associating the expected timeseries with the name as in
    tsd.

    >>> from nens.mock import Stream
    >>> root = parse_parameters(Stream('''<parameters><group>
    ... <model>Area</model>
    ... <parameter id="location_id"><stringValue>L1</stringValue></parameter>
    ... </group><group>
    ... <model>Bucket</model>
    ... <parameter id="location_id"><stringValue>B1</stringValue></parameter>
    ... </group><group>
    ... <model>Bucket</model>
    ... <parameter id="location_id"><stringValue>B2</stringValue></parameter>
    ... </group><group>
    ... <model>PumpingStation</model>
    ... <parameter id="location_id"><stringValue>PS1</stringValue></parameter>
    ... </group></parameters>'''))
    >>> tsd = {
    ... ('L1', 'NEERSG'): 1,
    ... ('L1', 'VERDPG'): 2,
    ... ('L1', 'KWEL'): 3,
    ... ('B1', 'NEERSG'): 4,
    ... ('B1', 'VERDPG'): 5,
    ... ('B1', 'KWEL'): 6,
    ... ('B2', 'NEERSG'): 7,
    ... ('B2', 'VERDPG'): 8,
    ... ('B2', 'KWEL'): 9,
    ... ('PS1', 'NEERSG'): 17,
    ... ('PS1', 'VERDPG'): 18,
    ... ('PS1', 'KWEL'): 19,
    ... }
    >>> k = {'Area': {'precipitation': 'NEERSG',
    ...  'evaporation': 'VERDPG',
    ...  'seepage': 'KWEL',
    ...  },
    ... 'Bucket': {'precipitation': 'NEERSG',
    ...  'evaporation': 'VERDPG',
    ...  'seepage': 'KWEL',
    ...  },
    ... 'PumpingStation': {'precipitation': 'NEERSG',
    ...  'evaporation': 'VERDPG',
    ...  'seepage': 'KWEL',
    ...  },
    ... }
    >>> type(attach_timeseries_to_structures(root, tsd, k))
    <class 'xmlmodel.snippets.Area'>
    >>> root.precipitation
    1
    >>> root.evaporation
    2
    >>> root.seepage
    3
    >>> [i.precipitation for i in root.bucket]
    [4, 7]
    >>> [i.precipitation for i in root.pumpingstation]
    [17]
    """

    for class_name in corresponding:
        if class_name == root.__class__.__name__:
            todo = [root]
        else:
            todo = getattr(root, class_name.lower())
        for local, remote in corresponding[class_name].items():
            for obj in todo:
                setattr(obj, local, tsd.get((obj.location_id, remote)))

    return root
