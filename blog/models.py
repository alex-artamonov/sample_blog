from django.db import models as m
from django.db.models.query import QuerySet
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from taggit.managers import TaggableManager




# class PublishedManager(m.Manager):
#     def get_queryset(self) -> QuerySet:
#         return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class PublishedManager(m.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)

# Create your models here.
class Post(m.Model):
    class Status(m.TextChoices):
        DRAFT = (
            "DF",
            "Draft",
        )
        PUBLISHED = "PB", "Published"

    title = m.CharField(max_length=200)
    slug = m.SlugField(max_length=200,
                        unique_for_date='publish')
    author = m.ForeignKey(User, on_delete=m.CASCADE, related_name="blog_posts")
    body = m.TextField()
    publish = m.DateTimeField(default=timezone.now)
    created = m.DateTimeField(auto_now_add=True)
    updated = m.DateTimeField(auto_now=True)
    status = m.CharField(max_length=2, choices=Status.choices, default=Status.DRAFT)
    objects = m.Manager()
    published = PublishedManager()
    tags = TaggableManager()

    class Meta:
        ordering = ["-publish"]
        indexes = [m.Index(fields=["-publish"])]

    def __str__(self) -> str:
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', 
                       args=[self.publish.year, 
                             self.publish.month,
                             self.publish.day,
                             self.slug])
        # return reverse('blog:post_detail2',
        #                args=[self.id])


class Comment(m.Model):
    post = m.ForeignKey(Post,
                        on_delete=m.CASCADE,
                        related_name='comments'
    )
    name = m.CharField(max_length=80)
    email = m.EmailField()
    body = m.TextField()
    created = m.DateTimeField(auto_now_add=True)
    updated = m.DateTimeField(auto_now=True)
    active = m.BooleanField(default=True)
    class Meta:
        ordering = ['created']
        indexes = [
            m.Index(fields=['created']),
        ]
        def __str__(self) -> str:
            return f'Comment on {self.name} on {self.post}'
