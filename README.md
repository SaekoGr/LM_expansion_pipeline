# Language model adaptation pipeline
This is script for automatic language model adaptation pipeline. This script is built with Python native modules, but it requires manual installation of the [SRILM toolkit](http://www.speech.sri.com/projects/srilm/download.html) to be used. In order to install the required Python modules, firstly run: 

`pip install -r requirements.txt`

Once SRILM toolkit and python modules are installed, the pipeline can be initialized. There are 2 ways to run the pipeline:
- run single adaptation by callinng `lm_pipeline(config, fingerprint, preferred_type)` from the `lm_pipeline.py` file. The only mandatory parameter is the absolute path to the configuration file in `config` and other values are by default `None`. If no `fingerprint` is given, it is created as a hash of the input parameters. `preferred_type` can be `None, stt, kws` or `file`.
- run multiple experiments by calling the `experiments_runner.py` script with path to the configuration file and the name of the experiments log file.

There are 2 samples of the configuration file included in this repository. The file `sample_single.json` is an example of the configuration file for a single run of the pipeline. The other file named `sample_exp.json` is an example of the configuration file for a run of multiple experiments.

For a full description of each parameter, please refer to the file located in a `doc` subfolder.