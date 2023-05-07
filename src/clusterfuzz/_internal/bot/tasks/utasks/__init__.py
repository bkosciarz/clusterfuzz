# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for executing the different parts of a utask."""

from clusterfuzz._internal.bot.tasks.utasks import uworker_io

def tworker_preprocess(task_module, task_argument, job_type, uworker_env):
  # Do preprocessing.
  uworker_input = task_module.preprocess_task(task_argument, job_type,
                                              uworker_env)
  if not uworker_input:
    # Bail if preprocessing failed since we can't proceed.
    return None, None

  # Get URLs for the uworker's output. We need a signed upload URL so it can
  # write its output. Also get a download URL in case the caller wants to read
  # the output.
  uworker_output_upload_url, uworker_output_download_url = (
      uworker_io.get_uworker_output_upload_urls())

  # Write the uworker's input to GCS and get the URL to download the input in
  # case the caller needs it.
  uworker_input_download_url = uworker_io.serialize_and_upload_uworker_input(
      uworker_input, job_type, uworker_output_upload_url)

  # Return the uworker_input_download_url for the remote executor to pass to the
  # batch job and for the local executor to download locally. Return
  # uworker_output_download_url for the local executor to download the output
  # after local execution of the utask_main.
  return uworker_input_download_url, uworker_output_download_url


def uworker_main(task_module, input_download_url):
  """Exectues the main part of a utask on the uworker (locally if not using
  remote executor)."""
  uworker_input = download_and_deserialize_uworker_input(input_download_url)
  uworker_output_upload_url = uworker_input.pop('uworker_output_upload_url')
  uworker_output = task_module.uworker_main(**uworker_input)
  uworker_io.serialize_and_upload_uworker_output(
      uworker_output, uworker_output_upload_url)


def tworker_postprocess(task_module, output_download_url):
  """Executes the postprocess step on the trusted (t)worker."""
  uworker_output = uworker_io.download_and_deserialize_uworker_output(
      output_download_url)
  task_module.utask_postprocess(**uworker_output)
