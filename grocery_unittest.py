import unittest.mock

import click.testing

import grocery as module_ut

_ = unittest.mock.sentinel


def mymock(return_value, spec=None):
    if spec is None:
        spec = []
    return unittest.mock.Mock(return_value=return_value, spec=spec)


class TestModule(unittest.TestCase):
    def test_empty(self):
        runner = click.testing.CliRunner()
        mock_write_json = mymock(None)
        mock_lock = unittest.mock.MagicMock()
        with unittest.mock.patch('grocery._write_json', mock_write_json
                ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
                ):
            result = runner.invoke(module_ut.cart, ['empty'])
        self.assertEqual(0, result.exit_code)
        self.assertEqual('Cart cleared.\n', result.output)
        mock_write_json.assert_called_once_with({}, True)
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)

    def test_view_empty(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({})
        with unittest.mock.patch('grocery._read_json', mock_read_json
                ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
                ):
            result = runner.invoke(module_ut.cart, ['view'])
        self.assertEqual(0, result.exit_code)
        self.assertEqual('Empty.\n', result.output)
        mock_read_json.assert_called_once_with(True)
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)

    def test_view(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({2: {'Name': 'Wine',
            'Unit of Measure': 'Bottles', 'Quantity': 2, 'Price': 9.99}})
        with unittest.mock.patch('grocery._read_json', mock_read_json
                ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
                ):
            result = runner.invoke(module_ut.cart, ['view'])
        self.assertEqual(
            ' ID | Name | Unit of Measure | Quantity | Price | Subtotal\n'
            '-----------------------------------------------------------\n'
            ' 2  | Wine | Bottles         | 2        | $9.99 | $19.98  \n'
            '----------------------------------------------------------\n'
            '      Total                                        $19.98  \n',
            result.output
        )
        self.assertEqual(0, result.exit_code)
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)

    def test_remove(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
              ), unittest.mock.patch('grocery._write_json', mock_write_json
              ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
              ):
            result = runner.invoke(module_ut.cart, ['remove', '1'])
        self.assertEqual(0, result.exit_code)
        self.assertEqual('', result.output)
        mock_write_json.assert_called_once_with({2: _.row_b}, True)
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)

    def test_update_quantity(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        cart = {1: _.row_a, 2: _.row_b,
            3: {'Name': 'pizza', 'Price': 6.0, 'Unit of Measure': 'pies',
                'Quantity': 1.0}
        }
        mock_read_json = mymock(cart)
        ret = cart.copy()
        ret[3] = ret[3].copy()
        ret[3]['Quantity'] = 2.0
        mock_write_json = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
              ), unittest.mock.patch('grocery._write_json', mock_write_json
              ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
              ):
            result = runner.invoke(module_ut.cart,
                      ['update_quantity', '3', '2'])
        self.assertEqual(0, result.exit_code)
        self.assertEqual('', result.output)
        mock_write_json.assert_called_once_with(ret)
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)

    def test_add_item(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({2: _.row_a})
        mock_read_json = unittest.mock.Mock(spec=[],
          side_effect=lambda cart: ({2: _.row_a} if cart else {3: _.row_b})
        )
        mock_write_json = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
              ), unittest.mock.patch('grocery._write_json', mock_write_json
              ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
              ):
            result = runner.invoke(module_ut.cart,
                    ['add_item', 'pizza', 'pies', '6']
            )
        self.assertEqual(0, result.exit_code)
        self.assertEqual('', result.output)
        self.assertEqual(len(mock_write_json.call_args_list), 2)
        self.assertEqual(mock_write_json.call_args_list[0],
                unittest.mock.call({3: _.row_b, 4: {'Price': 6.0,
                    'Name': 'pizza', 'Unit of Measure': 'pies'}}, False))
        self.assertEqual(mock_write_json.call_args_list[1],
                unittest.mock.call({2: _.row_a, 3: {'Quantity': 1.0,
                    'product_id': 4}}, True
                    ))
        self.assertTrue(mock_lock.called)

    def test_add_item_bad_price(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
              ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
              ), unittest.mock.patch('grocery._write_json', mock_write_json
              ):
            result = runner.invoke(module_ut.cart,
                    ['add_item', 'name', 'unit', '--', '-1.2'])
        self.assertEqual(2, result.exit_code)
        self.assertFalse(mock_write_json.called)
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)

    def test_add_item_bad_quanity(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
              ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
              ), unittest.mock.patch('grocery._write_json', mock_write_json
              ):
            result = runner.invoke(module_ut.cart,
                    ['add_item', 'name', 'unit', '2', '--', '-1'])
        self.assertEqual(2, result.exit_code)
        self.assertFalse(mock_write_json.called)
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)

    def test_update_bad_quantity(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
              ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
              ), unittest.mock.patch('grocery._write_json', mock_write_json
              ):
            result = runner.invoke(module_ut.cart,
                    ['update_quantity', '2', '--', '-1'])
        self.assertEqual(2, result.exit_code)
        self.assertFalse(mock_write_json.called)
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)

    def test_update_bad_id(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
              ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
              ), unittest.mock.patch('grocery._write_json', mock_write_json
              ):
            result = runner.invoke(module_ut.cart,
                    ['update_quantity', '3', '1.2'])
        self.assertEqual(2, result.exit_code)
        self.assertFalse(mock_write_json.called)
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)

    def test_sleep(self):
        runner = click.testing.CliRunner()
        mock_sleep = mymock(None)
        mock_lock = unittest.mock.MagicMock()
        with unittest.mock.patch('grocery.time.sleep', mock_sleep
              ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
              ):
            result = runner.invoke(module_ut.cart, ['sleep'])
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)
        mock_sleep.assert_called_once_with(10)
        self.assertEqual(0, result.exit_code)

    def test_remove_bad_key(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
              ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
              ), unittest.mock.patch('grocery._write_json', mock_write_json
              ):
            result = runner.invoke(module_ut.cart, ['remove', '3'])
        mock_lock.assert_called_once_with('grocery cart lock', timeout=5)
        self.assertEqual(2, result.exit_code)
        self.assertFalse(mock_write_json.called)

    def test_billing_prompt(self):
        runner = click.testing.CliRunner()
        @module_ut.cart.command()
        @click.argument('prompt')
        @click.argument('pattern')
        def test_prompt(prompt, pattern):
            click.echo(module_ut.billing_prompt(prompt, pattern))
        result = runner.invoke(module_ut.cart, ['test_prompt', 'what?', r'^reg[e3]x$'],
                input='regex')
        self.assertEqual(result.output, 'what?: regex\nregex\n')
        self.assertEqual(0, result.exit_code)
        result = runner.invoke(module_ut.cart, ['test_prompt', 'what?', r'^reg[e3]x$'],
                input='no match')
        self.assertEqual(2, result.exit_code)
        result = runner.invoke(module_ut.cart, ['test_prompt', 'what?', r'^reg[e3]x$'],
                input='reg3x')
        self.assertEqual(result.output, 'what?: reg3x\nreg3x\n')
        self.assertEqual(0, result.exit_code)

    def test_card_payment_empty_cart(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({})
        mock_write_json = mymock(None)
        mock_card_auth = mymock(None)
        mock_view = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
                  ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
                  ), unittest.mock.patch('grocery._card_auth', mock_card_auth
                  ), unittest.mock.patch('grocery._view', mock_view
                  ), unittest.mock.patch('grocery._write_json', mock_write_json
                  ):
            result = runner.invoke(module_ut.cart, ['checkout', 'card'],
                    input='1111222233334567\n123\n0719\n97330\nfake addy\ny\n')
        self.assertFalse(mock_card_auth.called)
        self.assertFalse(mock_write_json.called)
        self.assertTrue(mock_lock.called)
        self.assertEqual(0, result.exit_code)

    def test_card_payment_abort(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        mock_card_auth = mymock(None)
        mock_view = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
                  ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
                  ), unittest.mock.patch('grocery._card_auth', mock_card_auth
                  ), unittest.mock.patch('grocery._view', mock_view
                  ), unittest.mock.patch('grocery._write_json', mock_write_json
                  ):
            result = runner.invoke(module_ut.cart, ['checkout', 'card'],
                    input='1111222233334567\n123\n0719\n97330\nfake addy\nn\n')
        mock_card_auth.assert_called_once_with('1111222233334567', '123', '0719',
            '97330')
        self.assertFalse(mock_write_json.called)
        mock_view.assert_called_once_with(True, 'ID',
                data={1: _.row_a, 2: _.row_b})
        self.assertTrue(mock_lock.called)
        self.assertEqual(0, result.exit_code)

    def test_paypal_payment_no_addy(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        mock_card_auth = mymock(None)
        mock_view = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
                  ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
                  ), unittest.mock.patch('grocery._card_auth', mock_card_auth
                  ), unittest.mock.patch('grocery._view', mock_view
                  ), unittest.mock.patch('grocery._write_json', mock_write_json
                  ):
            result = runner.invoke(module_ut.cart, ['checkout', 'paypal'],
                    input='cameron@cameronpallen.com\nn\nfake address\ny\n')
        mock_write_json.assert_called_once_with({}, True)
        self.assertFalse(mock_card_auth.called)
        mock_view.assert_called_once_with(True, 'ID',
                data={1: _.row_a, 2: _.row_b})
        self.assertTrue(mock_lock.called)
        self.assertEqual(0, result.exit_code)

    def test_paypal_payment(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        mock_card_auth = mymock(None)
        mock_view = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
                  ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
                  ), unittest.mock.patch('grocery._card_auth', mock_card_auth
                  ), unittest.mock.patch('grocery._view', mock_view
                  ), unittest.mock.patch('grocery._write_json', mock_write_json
                  ):
            result = runner.invoke(module_ut.cart, ['checkout', 'paypal'],
                    input='cameron@cameronpallen.com\ny\ny\n')
        mock_write_json.assert_called_once_with({}, True)
        self.assertFalse(mock_card_auth.called)
        mock_view.assert_called_once_with(True, 'ID',
                data={1: _.row_a, 2: _.row_b})
        self.assertTrue(mock_lock.called)
        self.assertEqual(0, result.exit_code)

    def test_card_payment(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        mock_card_auth = mymock(None)
        mock_view = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
                  ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
                  ), unittest.mock.patch('grocery._card_auth', mock_card_auth
                  ), unittest.mock.patch('grocery._view', mock_view
                  ), unittest.mock.patch('grocery._write_json', mock_write_json
                  ):
            result = runner.invoke(module_ut.cart, ['checkout', 'card'],
                    input='1111222233334567\n123\n0719\n97330\nfake addy\ny\n')
        mock_card_auth.assert_called_once_with('1111222233334567', '123', '0719',
            '97330')
        mock_write_json.assert_called_once_with({}, True)
        mock_view.assert_called_once_with(True, 'ID',
                data={1: _.row_a, 2: _.row_b})
        self.assertTrue(mock_lock.called)
        self.assertEqual(0, result.exit_code)

    def test_card_payment_bad_month(self):
        runner = click.testing.CliRunner()
        mock_lock = unittest.mock.MagicMock()
        mock_read_json = mymock({1: _.row_a, 2: _.row_b})
        mock_write_json = mymock(None)
        mock_card_auth = mymock(None)
        mock_view = mymock(None)
        with unittest.mock.patch('grocery._read_json', mock_read_json
                  ), unittest.mock.patch('grocery.ilock.ILock', mock_lock
                  ), unittest.mock.patch('grocery._card_auth', mock_card_auth
                  ), unittest.mock.patch('grocery._view', mock_view
                  ), unittest.mock.patch('grocery._write_json', mock_write_json
                  ):
            result = runner.invoke(module_ut.cart, ['checkout', 'card'],
                    input='1111222233334567\n123\n2119\n97330\nfake addy\ny\n')
        self.assertFalse(mock_card_auth.called)
        self.assertFalse(mock_write_json.called)
        self.assertTrue(mock_lock.called)
        self.assertEqual(2, result.exit_code)

    def test_auth_card(self):
        module_ut._card_auth(_.number, _.code, _.expiry, _.zip)


if __name__ == '__main__':
    unittest.main()
