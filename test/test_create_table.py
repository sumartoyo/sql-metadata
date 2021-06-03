import pytest

from sql_metadata import Parser
from sql_metadata.keywords_lists import QueryType


def test_is_create_table_query():
    with pytest.raises(ValueError):
        assert Parser("BEGIN").query_type

    assert Parser("SELECT * FROM `foo` ()").query_type == QueryType.SELECT
    assert Parser("CREATE TABLE `foo` ()").query_type == QueryType.CREATE
    assert (
        Parser(
            "CREATE table abc.foo as SELECT pqr.foo1 , ab.foo2 FROM foo pqr, bar ab"
        ).query_type
        == QueryType.CREATE
    )


def test_create_table():
    parser = Parser(
        """
CREATE TABLE `new_table` (
    `item_id` int(9) NOT NULL AUTO_INCREMENT,
    `foo` varchar(16) NOT NULL DEFAULT '',
    PRIMARY KEY (`item_id`,`foo`),
    KEY `idx_foo` (`foo`)
) CHARACTER SET utf8;
    """
    )

    assert parser.tables == ["new_table"]
    assert parser.columns == ["item_id", "foo"]


def test_simple_create_table_as_select():
    parser = Parser(
        """
CREATE table abc.foo
    as SELECT pqr.foo1 , ab.foo2
    FROM foo pqr, bar ab;
    """
    )

    assert parser.tables == ["abc.foo", "foo", "bar"]
    assert parser.columns == ["foo.foo1", "bar.foo2"]


def test_create_table_as_select_with_joins():
    qry = """
        CREATE table xyz as 
        SELECT *
        from table_a
        join table_b on (table_a.name = table_b.name)
        left join table_c on (table_a.age = table_c.age)
        order by table_a.name, table_a.age
        """
    parser = Parser(qry)
    assert parser.columns == [
        "*",
        "table_a.name",
        "table_b.name",
        "table_a.age",
        "table_c.age",
    ]
    assert parser.tables == ["xyz", "table_a", "table_b", "table_c"]


def test_creating_table_as_select_with_with_clause():
    qry = """
        CREATE table xyz as 
        with sub as (select it_id from internal_table)
        SELECT *
        from table_a
        join table_b on (table_a.name = table_b.name)
        left join table_c on (table_a.age = table_c.age)
        left join sub on (table.it_id = sub.it_id)
        order by table_a.name, table_a.age
        """
    parser = Parser(qry)
    assert parser.with_names == ["sub"]
    assert parser.columns == [
        "it_id",
        "*",
        "table_a.name",
        "table_b.name",
        "table_a.age",
        "table_c.age",
        "table.it_id",
        "sub.it_id",
    ]
    assert parser.tables == ["xyz", "internal_table", "table_a", "table_b", "table_c"]
