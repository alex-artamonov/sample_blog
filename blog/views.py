from django.shortcuts import render, get_object_or_404
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from .models import Post, Comment
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from .forms import EmailPostForm, CommentForm, SearchForm
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from mysite import env


def post_list(request, tag_slug=None):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', 'body')
            search_query = SearchQuery(query)
            results = Post.published.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
                ).filter(search=search_query).order_by('-rank')
        
    else:
        post_list = Post.published.all()
        paginator = Paginator(post_list, 3)
        page_number = request.GET.get('page', 1)
        tag = None
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            post_list = post_list.filter(tags__in=[tag])
        # posts = paginator.page(page_number)
        paginator = Paginator(post_list, 3)
        page_number = request.GET.get('page', 1)
        try:
            posts = paginator.page(page_number)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)
        return render(request, "blog/post/list.html", {"posts": posts,
                                                   "tag":tag})
    if form:
        return render(request, 'blog/post/search.html',
                  {'form': form,
                      'query': query,
                      'results': results})


def post_detail(request, year, month, day, post):
    try:
        post = Post.published.get(slug=post,
                                  publish__year=year,
                                  publish__month=month,
                                  publish__day=day)
        comments = post.comments.filter(active=True)
        form = CommentForm()
        post_tags_id = post.tags.values_list('id', flat=True)
        similar_posts = Post.published.filter(tags__in=post_tags_id)\
            .exclude(id=post.id)
        similar_posts = similar_posts.annotate(same_tags=Count('tags'))\
            .order_by('-same_tags', '-publish')[:4]
    
    except Post.DoesNotExist:
        raise Http404("No post found, try harder")
    return render(request, "blog/post/post.html", {"post": post,
                                                   'comments': comments,
                                                   'form': form,
                                                   'similar_posts': similar_posts})


def post_detail2(request, id):
    post = get_object_or_404(Post, id=id, status=Post.Status.PUBLISHED)
    comments = post.comments.filter(active=True)
    form = CommentForm()
    #List of similar posts:
    post_tags_id = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_id).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=
                            Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request, "blog/post/post.html", {"post": post,
                                                   'comments': comments,
                                                   'form': form,
                                                   'similar_posts': similar_posts})


class PostListView(ListView):
    """Alternative post list view"""
    queryset = Post.published.all()
    model = Post
    context_object_name = 'posts'
    paginate_by = 3
    template_name = "blog/post/list.html"


def post_share(request, post_id):
    EMAIL_CONF = env.EMAIL_CONF
    print("=" * 50)
    print(EMAIL_CONF)
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)

    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, EMAIL_CONF["DEFAULT_FROM_EMAIL"],
                      [cd['to']])
            sent = True
    else:
        form = EmailPostForm()

    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(request, 'blog/post/comment.html',
                  {'post':post,
                   'form':form,
                   'comment':comment})

def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            # search_vector = SearchVector('title', 'body')
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = Post.published.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
                # ).filter(search=search_query).order_by('-rank')
                ).filter(rank__gte=0.3).order_by('-rank')
    return render(request, 'blog/post/search.html',
                  {'form': form,
                      'query': query,
                      'results': results})

def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query)
                ).filter(similarity__gte=0.1).order_by('-similarity')
    return render(request, 'blog/post/search.html',
                  {'form': form,
                      'query': query,
                      'results': results})

