from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

from django.db import connections
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from wallets.models import Wallet, WalletOperation


class ConcurrentOperationsTest(TransactionTestCase):
    """
    Тесты для проверки корректной обработки конкурентных операций.
    
    Используется TransactionTestCase вместо TestCase, так как:
    - TestCase использует транзакции, которые не видны в других потоках
    - TransactionTestCase коммитит изменения в БД, делая их доступными для всех потоков
    """
    
    def setUp(self):
        """Настройка тестового клиента и кошелька"""
        self.wallet = Wallet.objects.create(balance=Decimal('1000.00'))
        # Сохраняем UUID для использования в потоках
        self.wallet_uuid = str(self.wallet.id)
    
    def tearDown(self):
        """Закрываем все соединения к БД после теста"""
        # Закрываем все соединения к базе данных
        # Это необходимо для конкурентных тестов, чтобы избежать ошибок при удалении тестовой БД
        connections.close_all()
    
    def test_concurrent_deposits(self):
        """Тест конкурентных операций DEPOSIT"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        initial_balance = Decimal('1000.00')
        deposit_amount = Decimal('100.00')
        num_threads = 10
        
        def make_deposit():
            # Создаем отдельный клиент для каждого потока
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'DEPOSIT',
                    'amount': str(deposit_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                # Закрываем соединения к БД в этом потоке
                connections.close_all()
        
        # Выполняем конкурентные депозиты
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_deposit) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        # Все операции должны быть успешными
        self.assertTrue(all(results))
        
        # Проверяем финальный баланс
        self.wallet.refresh_from_db()
        expected_balance = initial_balance + (deposit_amount * num_threads)
        self.assertEqual(self.wallet.balance, expected_balance)
        
        # Проверяем количество операций
        operations_count = WalletOperation.objects.filter(wallet=self.wallet).count()
        self.assertEqual(operations_count, num_threads)
    
    def test_concurrent_withdraws_with_sufficient_balance(self):
        """Тест конкурентных операций WITHDRAW с достаточным балансом"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        initial_balance = Decimal('1000.00')
        withdraw_amount = Decimal('50.00')
        num_threads = 10  # 10 * 50 = 500, меньше чем 1000
        
        def make_withdraw():
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'WITHDRAW',
                    'amount': str(withdraw_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                connections.close_all()
        
        # Выполняем конкурентные снятия
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_withdraw) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        # Все операции должны быть успешными
        self.assertTrue(all(results))
        
        # Проверяем финальный баланс
        self.wallet.refresh_from_db()
        expected_balance = initial_balance - (withdraw_amount * num_threads)
        self.assertEqual(self.wallet.balance, expected_balance)
    
    def test_concurrent_mixed_operations(self):
        """Тест конкурентных смешанных операций (DEPOSIT и WITHDRAW)"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        initial_balance = Decimal('1000.00')
        deposit_amount = Decimal('100.00')
        withdraw_amount = Decimal('50.00')
        num_deposits = 10
        num_withdraws = 5
        
        def make_deposit():
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'DEPOSIT',
                    'amount': str(deposit_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                connections.close_all()
        
        def make_withdraw():
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'WITHDRAW',
                    'amount': str(withdraw_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                connections.close_all()
        
        # Выполняем конкурентные операции
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            # Добавляем депозиты
            for _ in range(num_deposits):
                futures.append(executor.submit(make_deposit))
            # Добавляем снятия
            for _ in range(num_withdraws):
                futures.append(executor.submit(make_withdraw))
            
            results = [future.result() for future in as_completed(futures)]
        
        # Все операции должны быть успешными
        self.assertTrue(all(results))
        
        # Проверяем финальный баланс
        self.wallet.refresh_from_db()
        expected_balance = initial_balance + (deposit_amount * num_deposits) - (withdraw_amount * num_withdraws)
        self.assertEqual(self.wallet.balance, expected_balance)
        
        # Проверяем количество операций
        operations_count = WalletOperation.objects.filter(wallet=self.wallet).count()
        self.assertEqual(operations_count, num_deposits + num_withdraws)
    
    def test_concurrent_withdraws_insufficient_balance(self):
        """Тест конкурентных операций WITHDRAW с недостаточным балансом"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        initial_balance = Decimal('1000.00')
        withdraw_amount = Decimal('200.00')
        num_threads = 10  # 10 * 200 = 2000, больше чем 1000
        
        def make_withdraw():
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': 'WITHDRAW',
                    'amount': str(withdraw_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK
            finally:
                connections.close_all()
        
        # Выполняем конкурентные снятия
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_withdraw) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        # Некоторые операции должны быть успешными, некоторые - нет
        successful = sum(results)
        failed = num_threads - successful
        
        # Должно быть хотя бы несколько успешных и несколько неуспешных
        self.assertGreater(successful, 0, "At least some withdrawals should succeed")
        self.assertGreater(failed, 0, "Some withdrawals should fail due to insufficient balance")
        
        # Проверяем, что баланс не стал отрицательным
        self.wallet.refresh_from_db()
        self.assertGreaterEqual(self.wallet.balance, Decimal('0.00'))
        
        # Проверяем, что баланс корректный (не больше чем было)
        self.assertLessEqual(self.wallet.balance, initial_balance)
        
        # Проверяем количество успешных операций
        operations_count = WalletOperation.objects.filter(wallet=self.wallet).count()
        self.assertEqual(operations_count, successful)
    
    def test_race_condition_prevention(self):
        """Тест предотвращения race condition при одновременных операциях"""
        url = reverse('wallets:wallet-operation', kwargs={'wallet_uuid': self.wallet.id})
        initial_balance = Decimal('1000.00')
        num_operations = 20
        operation_amount = Decimal('10.00')
        
        def make_operation(operation_type):
            client = APIClient()
            try:
                response = client.post(url, {
                    'operation_type': operation_type,
                    'amount': str(operation_amount)
                }, format='json')
                return response.status_code == status.HTTP_200_OK, operation_type
            finally:
                connections.close_all()
        
        # Выполняем много операций одновременно
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            # Чередуем DEPOSIT и WITHDRAW
            for i in range(num_operations):
                op_type = 'DEPOSIT' if i % 2 == 0 else 'WITHDRAW'
                futures.append(executor.submit(make_operation, op_type))
            
            results = [future.result() for future in as_completed(futures)]
        
        # Все операции должны быть успешными (баланс достаточен)
        all_successful = all(result[0] for result in results)
        self.assertTrue(all_successful, "All operations should succeed")
        
        # Проверяем финальный баланс
        self.wallet.refresh_from_db()
        # Подсчитываем ожидаемый баланс
        deposits = sum(1 for r in results if r[1] == 'DEPOSIT')
        withdraws = sum(1 for r in results if r[1] == 'WITHDRAW')
        expected_balance = initial_balance + (operation_amount * deposits) - (operation_amount * withdraws)
        
        self.assertEqual(self.wallet.balance, expected_balance)
        
        # Проверяем количество операций
        operations_count = WalletOperation.objects.filter(wallet=self.wallet).count()
        self.assertEqual(operations_count, num_operations)
    


