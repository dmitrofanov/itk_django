from decimal import Decimal
import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from wallets.models import Wallet, WalletOperation


class WalletDetailViewTest(TestCase):
    """Тесты для GET /api/v1/wallets/{uuid}"""
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.client = APIClient()
        self.wallet = Wallet.objects.create(balance=Decimal('1000.00'))
    
    def test_get_existing_wallet(self):
        """Тест получения существующего кошелька"""
        url = reverse('wallets:wallet-detail', kwargs={'wallet_uuid': self.wallet.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data['balance'])), self.wallet.balance)
        self.assertEqual(str(response.data['id']), str(self.wallet.id))
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
    
    def test_get_nonexistent_wallet(self):
        """Тест получения несуществующего кошелька"""
        fake_uuid = uuid.uuid4()
        url = reverse('wallets:wallet-detail', kwargs={'wallet_uuid': fake_uuid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_wallet_invalid_uuid_format(self):
        """Тест получения кошелька с невалидным UUID"""
        url = f'/api/v1/wallets/invalid-uuid/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_wallet_method_not_allowed(self):
        """Тест, что POST не разрешен для этого эндпоинта"""
        url = reverse('wallets:wallet-detail', kwargs={'wallet_uuid': self.wallet.id})
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class WalletOperationViewTest(TestCase):
    """Тесты для POST /api/v1/wallets/{uuid}/operation"""
    
    def setUp(self):
        """Настройка тестового клиента и кошелька"""
        self.client = APIClient()
        self.wallet = Wallet.objects.create(balance=Decimal('1000.00'))
    
    def test_deposit_operation_success(self):
        """Тест успешной операции DEPOSIT"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '500.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1500.00'))
        
        # Проверяем, что операция сохранена в истории
        operation = WalletOperation.objects.filter(wallet=self.wallet).first()
        self.assertIsNotNone(operation)
        self.assertEqual(operation.operation_type, 'DEPOSIT')
        self.assertEqual(operation.amount, Decimal('500.00'))
    
    def test_withdraw_operation_success(self):
        """Тест успешной операции WITHDRAW"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'operation_type': 'WITHDRAW',
            'amount': '300.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('700.00'))
        
        # Проверяем операцию в истории
        operation = WalletOperation.objects.filter(wallet=self.wallet).first()
        self.assertEqual(operation.operation_type, 'WITHDRAW')
        self.assertEqual(operation.amount, Decimal('300.00'))
    
    def test_withdraw_insufficient_balance(self):
        """Тест снятия при недостаточном балансе"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'operation_type': 'WITHDRAW',
            'amount': '2000.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Insufficient balance')
        
        # Проверяем, что баланс не изменился
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))
        
        # Проверяем, что операция не была создана
        self.assertFalse(WalletOperation.objects.filter(wallet=self.wallet).exists())
    
    def test_operation_nonexistent_wallet(self):
        """Тест операции с несуществующим кошельком"""
        fake_uuid = uuid.uuid4()
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': fake_uuid})
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '100.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Wallet not found')
    
    def test_operation_invalid_operation_type(self):
        """Тест операции с невалидным типом"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'operation_type': 'INVALID',
            'amount': '100.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('operation_type', response.data)
    
    def test_operation_missing_operation_type(self):
        """Тест операции без типа"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'amount': '100.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('operation_type', response.data)
    
    def test_operation_missing_amount(self):
        """Тест операции без суммы"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'operation_type': 'DEPOSIT'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)
    
    def test_operation_zero_amount(self):
        """Тест операции с нулевой суммой"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '0.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)
    
    def test_operation_negative_amount(self):
        """Тест операции с отрицательной суммой"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '-10.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)
    
    def test_operation_minimum_amount(self):
        """Тест операции с минимальной суммой (0.01)"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '0.01'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1000.01'))
    
    def test_multiple_operations_sequence(self):
        """Тест последовательности операций"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        
        # DEPOSIT 500
        response1 = self.client.post(url, {
            'operation_type': 'DEPOSIT',
            'amount': '500.00'
        }, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # WITHDRAW 200
        response2 = self.client.post(url, {
            'operation_type': 'WITHDRAW',
            'amount': '200.00'
        }, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # DEPOSIT 100
        response3 = self.client.post(url, {
            'operation_type': 'DEPOSIT',
            'amount': '100.00'
        }, format='json')
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        
        # Проверяем финальный баланс
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1400.00'))
        
        # Проверяем количество операций в истории
        operations_count = WalletOperation.objects.filter(wallet=self.wallet).count()
        self.assertEqual(operations_count, 3)
    
    def test_operation_response_structure(self):
        """Тест структуры ответа операции"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        data = {
            'operation_type': 'DEPOSIT',
            'amount': '250.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertIn('balance', response.data)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
        self.assertEqual(Decimal(str(response.data['balance'])), Decimal('1250.00'))
    
    def test_operation_method_not_allowed(self):
        """Тест, что GET не разрешен для этого эндпоинта"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

