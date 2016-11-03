from io import StringIO
from unittest import TestCase, main
from unittest.mock import patch

from neo4jupyter import Neo4Jupyter


class TestNeo4Jupyter(TestCase):

    def test_init(self):
        n4j = Neo4Jupyter()
        self.assertEqual('https://', n4j.vis_path[0:8])
        self.assertEqual(25, n4j.node.size)
        self.assertEqual(14, n4j.node.font)
        self.assertEqual('gray', n4j.edge.color)
        self.assertEqual(14, n4j.edge.font)
        self.assertEqual('<html>', n4j.template[0:6])

    @patch('neo4jupyter.open')
    @patch('neo4jupyter.path')
    def test_custom_init(self, mock_path, mock_open):
        mock_path.return_value.exists.return_value = True
        mock_open.return_value = StringIO()
        n4j = Neo4Jupyter(
            vis_path='my_cdn',
            nodes_size=1,
            nodes_font=2,
            edges_color='teal',
            edges_font=3,
            template='my_template'
        )
        self.assertEqual('my_cdn', n4j.vis_path)
        self.assertEqual(1, n4j.node.size)
        self.assertEqual(2, n4j.node.font)
        self.assertEqual('teal', n4j.edge.color)
        self.assertEqual(3, n4j.edge.font)
        self.assertEqual('', n4j.template)

if __name__ == '__main__':
    main()
