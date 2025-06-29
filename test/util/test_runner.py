#!/usr/bin/env python3
# Copyright 2014 BitPay Inc.
# Copyright 2016-present The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test framework for bitcoin utils.

Runs automatically during `ctest --test-dir build/`.

Can also be run manually."""

import argparse
import configparser
import difflib
import json
import logging
import os
import pprint
import subprocess
import sys

def main():
    config = configparser.ConfigParser()
    config.optionxform = str
    with open(os.path.join(os.path.dirname(__file__), "../config.ini"), encoding="utf8") as f:
        config.read_file(f)
    env_conf = dict(config.items('environment'))

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    verbose = args.verbose

    if verbose:
        level = logging.DEBUG
    else:
        level = logging.ERROR
    formatter = '%(asctime)s - %(levelname)s - %(message)s'
    # Add the format/level to the logger
    logging.basicConfig(format=formatter, level=level)

    bctester(os.path.join(env_conf["SRCDIR"], "test", "util", "data"), "bitcoin-util-test.json", env_conf)

def bctester(test_dir, input_basename, buildenv):
    """ Loads and parses the input file, runs all tests and reports results"""
    input_filename = os.path.join(test_dir, input_basename)
    with open(input_filename, encoding="utf8") as f:
        raw_data = f.read()
    input_data = json.loads(raw_data)

    failed_testcases = []

    for test_obj in input_data:
        try:
            bctest(test_dir, test_obj, buildenv)
            logging.info("PASSED: %s", test_obj["description"])
        except Exception:  # pylint: disable=broad-except
            logging.info("FAILED: %s", test_obj["description"])
            failed_testcases.append(test_obj["description"])

    if failed_testcases:
        error_message = "FAILED_TESTCASES:\n"
        error_message += pprint.pformat(failed_testcases, width=400)
        logging.error(error_message)
        sys.exit(1)
    else:
        sys.exit(0)

def bctest(test_dir, test_obj, buildenv):
    """Runs a single test, comparing output and RC to expected output and RC.

    Raises an error if input can't be read, executable fails, or output/RC
    are not as expected. Error is caught by bctester() and reported.
    """
    # Get the exec names and arguments
    execprog = os.path.join(buildenv["BUILDDIR"], "bin", test_obj["exec"] + buildenv["EXEEXT"])
    if test_obj["exec"] == "./bitcoin-util":
        execprog = os.getenv("BITCOINUTIL", default=execprog)
    elif test_obj["exec"] == "./bitcoin-tx":
        execprog = os.getenv("BITCOINTX", default=execprog)

    execargs = test_obj['args']
    execrun = [execprog] + execargs

    # Read the input data (if there is any)
    input_data = None
    if "input" in test_obj:
        filename = os.path.join(test_dir, test_obj["input"])
        with open(filename, encoding="utf8") as f:
            input_data = f.read()

    # Read the expected output data (if there is any)
    output_fn = None
    output_data = None
    output_type = None
    if "output_cmp" in test_obj:
        output_fn = test_obj['output_cmp']
        output_type = os.path.splitext(output_fn)[1][1:]  # output type from file extension (determines how to compare)
        try:
            with open(os.path.join(test_dir, output_fn), encoding="utf8") as f:
                output_data = f.read()
        except OSError:
            logging.error("Output file %s cannot be opened", output_fn)
            raise
        if not output_data:
            logging.error("Output data missing for %s", output_fn)
            raise Exception
        if not output_type:
            logging.error("Output file %s does not have a file extension", output_fn)
            raise Exception

    # Run the test
    try:
        res = subprocess.run(execrun, capture_output=True, text=True, input=input_data)
    except OSError as e:
        logging.error("OSError, Failed to execute %s: %s", execprog, e)
        raise
    except Exception as e:  # pylint: disable=broad-except
        logging.error("Unexpected error running %s: %s", execprog, e)
        traceback.print_exc()
        raise

    if output_data:
        data_mismatch, formatting_mismatch = False, False
        # Parse command output and expected output
        try:
            a_parsed = parse_output(res.stdout, output_type)
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error parsing command output as %s: '%s'; res: %s", output_type, str(e), str(res))
            raise
        try:
            b_parsed = parse_output(output_data, output_type)
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error parsing expected output %s as %s: %s", output_fn, output_type, e)
            raise
        # Compare data
        if a_parsed != b_parsed:
            logging.error("Output data mismatch for %s (format %s); res: %s", output_fn, output_type, str(res))
            data_mismatch = True
        # Compare formatting
        if res.stdout != output_data:
            error_message = f"Output formatting mismatch for {output_fn}:\nres: {str(res)}\n"
            error_message += "".join(difflib.context_diff(output_data.splitlines(True),
                                                          res.stdout.splitlines(True),
                                                          fromfile=output_fn,
                                                          tofile="returned"))
            logging.error(error_message)
            formatting_mismatch = True

        assert not data_mismatch and not formatting_mismatch

    # Compare the return code to the expected return code
    want_rc = 0
    if "return_code" in test_obj:
        want_rc = test_obj['return_code']
    if res.returncode != want_rc:
        logging.error("Return code mismatch for %s; res: %s", output_fn, str(res))
        raise RuntimeError("Return code mismatch")

    if "error_txt" in test_obj:
        want_error = test_obj["error_txt"]
        # A partial match instead of an exact match makes writing tests easier
        # and should be sufficient.
        if want_error not in res.stderr:
            logging.error("Error mismatch:\nExpected: %s\nReceived: %s\nres: %s", want_error, res.stderr.rstrip(), str(res))
            raise RuntimeError("Error mismatch")
    else:
        if res.stderr:
            logging.error("Unexpected error received: %s\nres: %s", res.stderr.rstrip(), str(res))
            raise RuntimeError("Unexpected error")


def parse_output(a, fmt):
    """Parse the output according to specified format.

    Raise an error if the output can't be parsed."""
    if fmt == 'json':  # json: compare parsed data
        return json.loads(a)
    elif fmt == 'hex':  # hex: parse and compare binary data
        return bytes.fromhex(a.strip())
    else:
        raise NotImplementedError("Don't know how to compare %s" % fmt)

if __name__ == '__main__':
    main()
