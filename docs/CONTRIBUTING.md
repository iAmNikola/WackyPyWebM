# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the owners of this repository before making a change.
Please note we have a [code of conduct](CODE_OF_CONDUCT.md), please follow it in all your interactions with the project.

## Development environment setup

To set up a development environment, please follow these steps:

1. Clone the repo
   ```bash
   git clone https://github.com/iAmNikola/WackyPyWebM
   ```

2. Install Python formatter and linter
   ```bash
   pip install -r requirements_dev.txt
   ```

3. Run `black` formatter when you are done with changing the files
   ```bash
   black *.py --line-length=120 --skip-string-normalization
   ```

## Issues and feature requests

You've found a bug in the source code, a mistake in the documentation or maybe you'd like a new feature? You can help us by [submitting an issue on GitHub](https://github.com/iAmNikola/WackyPyWebM/issues). Before you create an issue, make sure to search the issue archive -- your issue may have already been addressed!

Please try to create bug reports that are:

- _Reproducible._ Include steps to reproduce the problem.
- _Specific._ Include as much detail as possible: which version, what environment, etc.
- _Unique._ Do not duplicate existing opened issues.
- _Scoped to a Single Bug._ One bug per report.

**Even better: Submit a pull request with a fix or new feature!**

### How to submit a Pull Request

1. Search our repository for open or closed
   [Pull Requests](https://github.com/iAmNikola/WackyPyWebM/pulls)
   that relate to your submission. You don't want to duplicate effort.
2. Fork the project
3. Create your feature branch (`git checkout -b ft-amazing-feature`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin ft-amazing-feature`)
6. [Open a Pull Request](https://github.com/iAmNikola/WackyPyWebM/compare?expand=1)
