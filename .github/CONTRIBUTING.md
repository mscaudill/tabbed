# Contributing

**Thank you for your interest in making Tabbed better!**

- [Contributing Etiquette](#contributing-etiquette)
- [Creating an Issue](#creating-an-issue)
- [Creating a Pull Request](#creating-a-pull-request)
    * [Requirements](#requirements)
    * [Setup](#setup)
    * [Modifications](#modifications)
    * [Updating Documentation](#update-documentation)
    * [Review Process](#review-process)
- [Commit Message Guide](#commit-message-guide)


## Contributing Etiquette

Please see our [Contributor Code of Conduct](
https://github.com/mscaudill/tabbed/blob/master/CODE_OF_CONDUCT.md) for
information on our rules of conduct.

## Creating an Issue

We have created [issue templates](
https://github.com/mscaudill/tabbed/issues) for:

- Asking questions
- Filing bug reports
- Making feature requests
- Improving Tabbed's documentation

## Creating a Pull Request

> Note: We appreciate you taking the time to contribute! Before starting
> a pull request please discuss with us in the comments of an open issue.
> This helps use to identify what issues are being worked on to prevent
> duplicate effort.

### Requirements

1. PRs must have a reference url to an existing issue that describes why the
   issue or feature needs addressing.
2. PRs must pass code quality checks with `pylint` and pass static type
   checking with `mypy` where appropriate.
3. PRs must have unit test with `pytest` that cover the changed behavior.

### Setup

1. Open an issue to discuss the changes you would like to see in Tabbed.
2. Fork Tabbed's master branch and create a local branch for your change.
3. Sumbit your fantastic PR!

### Modifications

For documentation consistency, we ask that your modifications adhere to
[Google's code style](https://google.github.io/styleguide/pyguide.html) and
be formatted with [black](https://github.com/psf/black). Also, please use type
annotations where possible.

### Review Process

To expedite a review of your pull request, we ask that:
1. you reference the issue url your pull request is addressing.
2. you comment modifications so that we can quickly understand your
   changes/additions.
3. you provide tests that demonstrate that your modifications work.
