from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Post, Tag

class PostCreationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='testuser1', password='testpass123')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass123')
        self.user3 = User.objects.create_user(username='testuser3', password='testpass123')

        # Create some existing tags
        self.tag1 = Tag.objects.create(name='technology')
        self.tag2 = Tag.objects.create(name='programming')

    def test_create_post_with_multiple_tags_and_authors(self):
        """Test creating a post with multiple existing tags, new tags, and tagged authors"""
        self.client.login(username='testuser1', password='testpass123')

        post_data = {
            'title': 'Test Post with Multiple Tags',
            'content': 'This is a test post content.',
            'tags': [self.tag1.id, self.tag2.id],  # Select existing tags
            'new_tags': 'django, web development, testing',  # Add new tags
            'tagged_authors': [self.user2.id, self.user3.id],  # Tag multiple authors
        }

        response = self.client.post(reverse('create_post'), post_data)

        # Check if post was created successfully
        self.assertEqual(response.status_code, 302)  # Should redirect after successful creation

        # Get the created post
        post = Post.objects.get(title='Test Post with Multiple Tags')

        # Verify the post has the correct author
        self.assertEqual(post.author, self.user1)

        # Verify existing tags are attached
        self.assertIn(self.tag1, post.tags.all())
        self.assertIn(self.tag2, post.tags.all())

        # Verify new tags were created and attached
        django_tag = Tag.objects.get(name='django')
        web_dev_tag = Tag.objects.get(name='web development')
        testing_tag = Tag.objects.get(name='testing')

        self.assertIn(django_tag, post.tags.all())
        self.assertIn(web_dev_tag, post.tags.all())
        self.assertIn(testing_tag, post.tags.all())

        # Verify tagged authors
        self.assertIn(self.user2, post.tagged_authors.all())
        self.assertIn(self.user3, post.tagged_authors.all())

        # Verify total tag count (2 existing + 3 new = 5)
        self.assertEqual(post.tags.count(), 5)

        # Verify total tagged authors count
        self.assertEqual(post.tagged_authors.count(), 2)

    def test_create_post_with_duplicate_tags(self):
        """Test that duplicate tags are handled correctly"""
        self.client.login(username='testuser1', password='testpass123')

        post_data = {
            'title': 'Test Post with Duplicate Tags',
            'content': 'This is a test post content.',
            'tags': [self.tag1.id],  # Select existing tag
            'new_tags': 'technology, new-tag, technology',  # Include duplicate of existing tag
        }

        self.client.post(reverse('create_post'), post_data)

        # Get the created post
        post = Post.objects.get(title='Test Post with Duplicate Tags')

        # Verify that 'technology' appears only once
        technology_tags = [tag for tag in post.tags.all() if tag.name == 'technology']
        self.assertEqual(len(technology_tags), 1)

        # Verify total tag count (technology + new-tag = 2)
        self.assertEqual(post.tags.count(), 2)

    def test_edit_post_with_multiple_tags_and_authors(self):
        """Test editing a post with multiple tags and authors"""
        # First create a post
        self.client.login(username='testuser1', password='testpass123')

        post = Post.objects.create(
            title='Original Post',
            content='Original content',
            author=self.user1
        )
        post.tags.add(self.tag1)
        post.tagged_authors.add(self.user2)

        # Now edit the post
        edit_data = {
            'title': 'Updated Post Title',
            'content': 'Updated content',
            'tags': [self.tag2.id],  # Change to different existing tag
            'new_tags': 'updated-tag, another-tag',  # Add new tags
            'tagged_authors': [self.user3.id],  # Change tagged author
        }

        response = self.client.post(reverse('edit_post', args=[post.id]), edit_data)

        # Check if edit was successful
        self.assertEqual(response.status_code, 302)  # Should redirect after successful edit

        # Refresh post from database
        post.refresh_from_db()

        # Verify the post was updated
        self.assertEqual(post.title, 'Updated Post Title')
        self.assertEqual(post.content, 'Updated content')

        # Verify old tag was removed and new ones added
        self.assertNotIn(self.tag1, post.tags.all())  # Old tag removed
        self.assertIn(self.tag2, post.tags.all())  # New existing tag added

        # Verify new tags were created and attached
        updated_tag = Tag.objects.get(name='updated-tag')
        another_tag = Tag.objects.get(name='another-tag')
        self.assertIn(updated_tag, post.tags.all())
        self.assertIn(another_tag, post.tags.all())

        # Verify tagged authors were updated
        self.assertNotIn(self.user2, post.tagged_authors.all())  # Old author removed
        self.assertIn(self.user3, post.tagged_authors.all())  # New author added

        # Verify total counts
        self.assertEqual(post.tags.count(), 3)  # tag2 + updated-tag + another-tag
        self.assertEqual(post.tagged_authors.count(), 1)  # Only user3

    def test_edit_post_remove_all_tags_and_authors(self):
        """Test removing all tags and authors from a post"""
        self.client.login(username='testuser1', password='testpass123')

        # Create a post with tags and authors
        post = Post.objects.create(
            title='Post with Tags',
            content='Content',
            author=self.user1
        )
        post.tags.add(self.tag1, self.tag2)
        post.tagged_authors.add(self.user2, self.user3)

        # Edit to remove all tags and authors
        edit_data = {
            'title': 'Post without Tags',
            'content': 'Updated content',
            'tags': [],  # No tags selected
            'new_tags': '',  # No new tags
            'tagged_authors': [],  # No authors selected
        }

        self.client.post(reverse('edit_post', args=[post.id]), edit_data)

        # Refresh post from database
        post.refresh_from_db()

        # Verify all tags and authors were removed
        self.assertEqual(post.tags.count(), 0)
        self.assertEqual(post.tagged_authors.count(), 0)
