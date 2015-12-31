# Contributing

This project adheres to the Open Code of Conduct. By participating, you are expected to honor this code.

## Developing

The best way to start developing this project is to set up a virtualenv and install the requirements.

    git clone <my remote url/sodapy.git>
    cd sodapy
    virtualenv venv_sodapy
    source venv_sodapy/bin/activate
    pip install -r requirements.txt

If everything is set up correctly, tests to should pass:

    ./runtests tests/

## Submitting a Pull Request

1. Fork this repository.
2. Create a branch `git checkout -b my_feature`.
3. Commit your changes `git commit -am "Great new feature that closes #3"`. Reference any related issues in the first line of the commit message.
4. Push to remote `git push origin my_feature`.
5. Open a pull request.
6. Pat yourself on the back for making an open source contribution :) 

## Other considerations

- Please review the open issues before opening a PR.
- Significant changes or new features should be documented in [`README.md`](https://github.com/xmunoz/sodapy/blob/master/README.md).
- Writing tests is never a bad idea. Make sure all tests are passing before opening a PR.
