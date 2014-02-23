# Instant Coverage

Your new Django site need tests. Nothing super fancy, just enough that you know
it's not going to start 500ing next time you deploy. You *could* write unit
tests, but those are boring and your client sure as hell isn't going to pay for
the time.

You've got five minutes, though.

## Features

- **Simple**
    - Iterates through a list of URLs and complains if any of them 500.
- **Magic**
    - Will loudly complain when there are views missing from the list of URLs
      to test.
- **Has what you need**
    - Comes with optional tests for validating HTML to various degrees of
      strictness, hunting for dead links (both internal and external) and
      finding orphaned pages.
- **Extensible**
    - Easily add tests that will run against every view on your website. If you
      want tests for things like consistent capitalisation of a particular
      phrase or the universal inclusion of a particular meta tag, you can have
      them in minutes.

# Usage

## Setup

- pip
- settings
- import
- caching and overriding setUp
- fixtures

## Extending the base tests
