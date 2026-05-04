#!/usr/bin/env python
"""
Test de validation des avis selon les nouvelles spécifications:
- Le commentaire doit contenir au moins 5 caractères
- La note doit être sélectionnée (1-5)
"""

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from pages.models import Restaurant, Review

class AvisValidationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Créer un restaurant de test
        self.restaurant = Restaurant.objects.create(
            name='Restaurant Test',
            email='resto@test.com',
            status='approved',
            rating=4.0
        )
        
    def test_avis_commentaire_trop_court(self):
        """Test: commentaire de moins de 5 caractères doit être rejeté"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'restaurant_id': str(self.restaurant.id),
            'rating': 5,
            'comment': '1234',  # 4 caractères seulement
            'name': 'Test User'
        }
        
        response = self.client.post(
            '/api/submit-review/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Le commentaire doit contenir au moins 5 caractères', response_data['error'])
        
    def test_avis_commentaire_vide(self):
        """Test: commentaire vide doit être rejeté"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'restaurant_id': str(self.restaurant.id),
            'rating': 5,
            'comment': '',  # Commentaire vide
            'name': 'Test User'
        }
        
        response = self.client.post(
            '/api/submit-review/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Le commentaire doit contenir au moins 5 caractères', response_data['error'])
        
    def test_avis_commentaire_espaces_seulement(self):
        """Test: commentaire avec uniquement des espaces doit être rejeté"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'restaurant_id': str(self.restaurant.id),
            'rating': 5,
            'comment': '    ',  # Espaces seulement
            'name': 'Test User'
        }
        
        response = self.client.post(
            '/api/submit-review/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Le commentaire doit contenir au moins 5 caractères', response_data['error'])
        
    def test_avis_commentaire_valide(self):
        """Test: commentaire de 5 caractères ou plus doit être accepté"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'restaurant_id': str(self.restaurant.id),
            'rating': 5,
            'comment': '12345',  # Exactement 5 caractères
            'name': 'Test User'
        }
        
        response = self.client.post(
            '/api/submit-review/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        
    def test_avis_sans_note(self):
        """Test: avis sans note doit être rejeté"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'restaurant_id': str(self.restaurant.id),
            'rating': 0,  # Note invalide
            'comment': 'Un excellent restaurant !',
            'name': 'Test User'
        }
        
        response = self.client.post(
            '/api/submit-review/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Données invalides', response_data['error'])
        
    def test_avis_note_hors_limites(self):
        """Test: note hors de la plage 1-5 doit être rejetée"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'restaurant_id': str(self.restaurant.id),
            'rating': 6,  # Note hors limites
            'comment': 'Un excellent restaurant !',
            'name': 'Test User'
        }
        
        response = self.client.post(
            '/api/submit-review/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('Données invalides', response_data['error'])
        
    def test_avis_complet_valide(self):
        """Test: avis complet avec toutes les données valides"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'restaurant_id': str(self.restaurant.id),
            'rating': 4,
            'comment': 'Un restaurant vraiment excellent avec un service impeccable !',
            'name': 'Test User'
        }
        
        response = self.client.post(
            '/api/submit-review/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        self.assertIn('new_rating', response_data)
        
        # Vérifier que l'avis a été créé
        avis_count = Review.objects.filter(restaurant_id=str(self.restaurant.id)).count()
        self.assertEqual(avis_count, 1)

if __name__ == '__main__':
    import django
    django.setup()
    
    # Exécuter les tests
    import unittest
    unittest.main()