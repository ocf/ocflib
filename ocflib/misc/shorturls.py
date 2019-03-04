import functools
import re

from ocflib.infra import mysql


SHORTURL_SLUG_ALLOWED_CHARS = r'^[\w./+:-]+$'
SHORTURL_REGEX = re.compile(SHORTURL_SLUG_ALLOWED_CHARS)

get_connection = functools.partial(
    mysql.get_connection,
    db='ocfshorturls',
    user='anonymous',
    password=None,
)


def _validate_slug(slug):
    if len(slug) > 100:
        raise ValueError('shorturl len is {}, must be less than 100'.format(len(slug)))
    if not SHORTURL_REGEX.search(slug):
        raise ValueError("shorturl '{}' contains illegal characters".format(slug))


def get_shorturl(ctx, slug):
    """Get the target of a shorturl by its slug."""

    query = 'SELECT `target` FROM `shorturls_public` WHERE `slug` = %s'
    ctx.execute(query, (slug))

    candidate = ctx.fetchone()
    return candidate['target'] if candidate else None


def add_shorturl(ctx, slug, target):
    """Add a shorturl to the database."""

    _validate_slug(slug)

    # we don't need to explicitly check for duplicates because
    # there's a uniqueness constraint on the slug column
    query = 'INSERT INTO `shorturls` (slug, target) VALUES (%s, %s)'
    ctx.execute(query, (slug, target))


def delete_shorturl(ctx, slug):
    """Delete a shorturl from the database."""

    query = 'DELETE FROM `shorturls` WHERE `slug` = %s'
    ctx.execute(query, (slug,))


def rename_shorturl(ctx, old_slug, new_slug):
    """Rename a shorturl."""

    _validate_slug(new_slug)

    query = 'UPDATE `shorturls` SET `slug` = %s WHERE `slug` = %s'
    ctx.execute(query, (new_slug, old_slug))


def replace_shorturl(ctx, slug, new_target):
    """Change the target of a shorturl."""

    query = 'UPDATE `shorturls` SET `target` = %s WHERE `slug` = %s'
    ctx.execute(query, (new_target, slug))
