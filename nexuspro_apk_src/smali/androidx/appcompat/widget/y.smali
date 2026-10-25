.class public abstract Landroidx/appcompat/widget/y;
.super Landroid/view/ViewGroup;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Landroidx/appcompat/widget/y$a;
    }
.end annotation


# instance fields
.field private a:Z

.field private b:I

.field private c:I

.field private d:I

.field private e:I

.field private f:I

.field private g:F

.field private h:Z

.field private i:[I

.field private j:[I

.field private k:Landroid/graphics/drawable/Drawable;

.field private l:I

.field private m:I

.field private n:I

.field private o:I


# direct methods
.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    .locals 1

    const/4 v0, 0x0

    .line 1
    invoke-direct {p0, p1, p2, v0}, Landroidx/appcompat/widget/y;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V
    .locals 11

    .line 2
    invoke-direct {p0, p1, p2, p3}, Landroid/view/ViewGroup;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    const/4 v0, 0x1

    .line 3
    iput-boolean v0, p0, Landroidx/appcompat/widget/y;->a:Z

    const/4 v1, -0x1

    .line 4
    iput v1, p0, Landroidx/appcompat/widget/y;->b:I

    const/4 v2, 0x0

    .line 5
    iput v2, p0, Landroidx/appcompat/widget/y;->c:I

    const v3, 0x800033

    .line 6
    iput v3, p0, Landroidx/appcompat/widget/y;->e:I

    .line 7
    sget-object v3, Ld/i;->r0:[I

    invoke-static {p1, p2, v3, p3, v2}, Landroidx/appcompat/widget/K;->s(Landroid/content/Context;Landroid/util/AttributeSet;[III)Landroidx/appcompat/widget/K;

    move-result-object v3

    .line 8
    sget-object v6, Ld/i;->r0:[I

    .line 9
    invoke-virtual {v3}, Landroidx/appcompat/widget/K;->o()Landroid/content/res/TypedArray;

    move-result-object v8

    const/4 v10, 0x0

    move-object v4, p0

    move-object v5, p1

    move-object v7, p2

    move v9, p3

    .line 10
    invoke-static/range {v4 .. v10}, Landroidx/core/view/v;->v(Landroid/view/View;Landroid/content/Context;[ILandroid/util/AttributeSet;Landroid/content/res/TypedArray;II)V

    .line 11
    sget p1, Ld/i;->t0:I

    invoke-virtual {v3, p1, v1}, Landroidx/appcompat/widget/K;->i(II)I

    move-result p1

    if-ltz p1, :cond_0

    .line 12
    invoke-virtual {p0, p1}, Landroidx/appcompat/widget/y;->setOrientation(I)V

    .line 13
    :cond_0
    sget p1, Ld/i;->s0:I

    invoke-virtual {v3, p1, v1}, Landroidx/appcompat/widget/K;->i(II)I

    move-result p1

    if-ltz p1, :cond_1

    .line 14
    invoke-virtual {p0, p1}, Landroidx/appcompat/widget/y;->setGravity(I)V

    .line 15
    :cond_1
    sget p1, Ld/i;->u0:I

    invoke-virtual {v3, p1, v0}, Landroidx/appcompat/widget/K;->a(IZ)Z

    move-result p1

    if-nez p1, :cond_2

    .line 16
    invoke-virtual {p0, p1}, Landroidx/appcompat/widget/y;->setBaselineAligned(Z)V

    .line 17
    :cond_2
    sget p1, Ld/i;->w0:I

    const/high16 p2, -0x40800000    # -1.0f

    invoke-virtual {v3, p1, p2}, Landroidx/appcompat/widget/K;->g(IF)F

    move-result p1

    iput p1, v4, Landroidx/appcompat/widget/y;->g:F

    .line 18
    sget p1, Ld/i;->v0:I

    .line 19
    invoke-virtual {v3, p1, v1}, Landroidx/appcompat/widget/K;->i(II)I

    move-result p1

    iput p1, v4, Landroidx/appcompat/widget/y;->b:I

    .line 20
    sget p1, Ld/i;->z0:I

    invoke-virtual {v3, p1, v2}, Landroidx/appcompat/widget/K;->a(IZ)Z

    move-result p1

    iput-boolean p1, v4, Landroidx/appcompat/widget/y;->h:Z

    .line 21
    sget p1, Ld/i;->x0:I

    invoke-virtual {v3, p1}, Landroidx/appcompat/widget/K;->f(I)Landroid/graphics/drawable/Drawable;

    move-result-object p1

    invoke-virtual {p0, p1}, Landroidx/appcompat/widget/y;->setDividerDrawable(Landroid/graphics/drawable/Drawable;)V

    .line 22
    sget p1, Ld/i;->A0:I

    invoke-virtual {v3, p1, v2}, Landroidx/appcompat/widget/K;->i(II)I

    move-result p1

    iput p1, v4, Landroidx/appcompat/widget/y;->n:I

    .line 23
    sget p1, Ld/i;->y0:I

    invoke-virtual {v3, p1, v2}, Landroidx/appcompat/widget/K;->e(II)I

    move-result p1

    iput p1, v4, Landroidx/appcompat/widget/y;->o:I

    .line 24
    invoke-virtual {v3}, Landroidx/appcompat/widget/K;->u()V

    return-void
.end method

.method private f(II)V
    .locals 9

    .line 1
    invoke-virtual {p0}, Landroid/view/View;->getMeasuredHeight()I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    const/high16 v1, 0x40000000    # 2.0f

    .line 6
    .line 7
    invoke-static {v0, v1}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    .line 8
    .line 9
    .line 10
    move-result v6

    .line 11
    const/4 v0, 0x0

    .line 12
    :goto_0
    if-ge v0, p1, :cond_1

    .line 13
    .line 14
    invoke-virtual {p0, v0}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    .line 15
    .line 16
    .line 17
    move-result-object v3

    .line 18
    invoke-virtual {v3}, Landroid/view/View;->getVisibility()I

    .line 19
    .line 20
    .line 21
    move-result v1

    .line 22
    const/16 v2, 0x8

    .line 23
    .line 24
    if-eq v1, v2, :cond_0

    .line 25
    .line 26
    invoke-virtual {v3}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 27
    .line 28
    .line 29
    move-result-object v1

    .line 30
    check-cast v1, Landroidx/appcompat/widget/y$a;

    .line 31
    .line 32
    iget v2, v1, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 33
    .line 34
    const/4 v4, -0x1

    .line 35
    if-ne v2, v4, :cond_0

    .line 36
    .line 37
    iget v8, v1, Landroid/widget/LinearLayout$LayoutParams;->width:I

    .line 38
    .line 39
    invoke-virtual {v3}, Landroid/view/View;->getMeasuredWidth()I

    .line 40
    .line 41
    .line 42
    move-result v2

    .line 43
    iput v2, v1, Landroid/widget/LinearLayout$LayoutParams;->width:I

    .line 44
    .line 45
    const/4 v5, 0x0

    .line 46
    const/4 v7, 0x0

    .line 47
    move-object v2, p0

    .line 48
    move v4, p2

    .line 49
    invoke-virtual/range {v2 .. v7}, Landroid/view/ViewGroup;->measureChildWithMargins(Landroid/view/View;IIII)V

    .line 50
    .line 51
    .line 52
    iput v8, v1, Landroid/widget/LinearLayout$LayoutParams;->width:I

    .line 53
    .line 54
    goto :goto_1

    .line 55
    :cond_0
    move v4, p2

    .line 56
    :goto_1
    add-int/lit8 v0, v0, 0x1

    .line 57
    .line 58
    move p2, v4

    .line 59
    goto :goto_0

    .line 60
    :cond_1
    return-void
.end method

.method private g(II)V
    .locals 9

    .line 1
    invoke-virtual {p0}, Landroid/view/View;->getMeasuredWidth()I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    const/high16 v1, 0x40000000    # 2.0f

    .line 6
    .line 7
    invoke-static {v0, v1}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    .line 8
    .line 9
    .line 10
    move-result v4

    .line 11
    const/4 v0, 0x0

    .line 12
    :goto_0
    if-ge v0, p1, :cond_1

    .line 13
    .line 14
    invoke-virtual {p0, v0}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    .line 15
    .line 16
    .line 17
    move-result-object v3

    .line 18
    invoke-virtual {v3}, Landroid/view/View;->getVisibility()I

    .line 19
    .line 20
    .line 21
    move-result v1

    .line 22
    const/16 v2, 0x8

    .line 23
    .line 24
    if-eq v1, v2, :cond_0

    .line 25
    .line 26
    invoke-virtual {v3}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 27
    .line 28
    .line 29
    move-result-object v1

    .line 30
    check-cast v1, Landroidx/appcompat/widget/y$a;

    .line 31
    .line 32
    iget v2, v1, Landroid/widget/LinearLayout$LayoutParams;->width:I

    .line 33
    .line 34
    const/4 v5, -0x1

    .line 35
    if-ne v2, v5, :cond_0

    .line 36
    .line 37
    iget v8, v1, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 38
    .line 39
    invoke-virtual {v3}, Landroid/view/View;->getMeasuredHeight()I

    .line 40
    .line 41
    .line 42
    move-result v2

    .line 43
    iput v2, v1, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 44
    .line 45
    const/4 v5, 0x0

    .line 46
    const/4 v7, 0x0

    .line 47
    move-object v2, p0

    .line 48
    move v6, p2

    .line 49
    invoke-virtual/range {v2 .. v7}, Landroid/view/ViewGroup;->measureChildWithMargins(Landroid/view/View;IIII)V

    .line 50
    .line 51
    .line 52
    iput v8, v1, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 53
    .line 54
    goto :goto_1

    .line 55
    :cond_0
    move v6, p2

    .line 56
    :goto_1
    add-int/lit8 v0, v0, 0x1

    .line 57
    .line 58
    move p2, v6

    .line 59
    goto :goto_0

    .line 60
    :cond_1
    return-void
.end method

.method private v(Landroid/view/View;IIII)V
    .locals 0

    .line 1
    add-int/2addr p4, p2

    .line 2
    add-int/2addr p5, p3

    .line 3
    invoke-virtual {p1, p2, p3, p4, p5}, Landroid/view/View;->layout(IIII)V

    .line 4
    .line 5
    .line 6
    return-void
.end method


# virtual methods
.method b(Landroid/graphics/Canvas;)V
    .locals 6

    .line 1
    invoke-virtual {p0}, Landroidx/appcompat/widget/y;->getVirtualChildCount()I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    invoke-static {p0}, Landroidx/appcompat/widget/W;->a(Landroid/view/View;)Z

    .line 6
    .line 7
    .line 8
    move-result v1

    .line 9
    const/4 v2, 0x0

    .line 10
    :goto_0
    if-ge v2, v0, :cond_2

    .line 11
    .line 12
    invoke-virtual {p0, v2}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    .line 13
    .line 14
    .line 15
    move-result-object v3

    .line 16
    if-eqz v3, :cond_1

    .line 17
    .line 18
    invoke-virtual {v3}, Landroid/view/View;->getVisibility()I

    .line 19
    .line 20
    .line 21
    move-result v4

    .line 22
    const/16 v5, 0x8

    .line 23
    .line 24
    if-eq v4, v5, :cond_1

    .line 25
    .line 26
    invoke-virtual {p0, v2}, Landroidx/appcompat/widget/y;->o(I)Z

    .line 27
    .line 28
    .line 29
    move-result v4

    .line 30
    if-eqz v4, :cond_1

    .line 31
    .line 32
    invoke-virtual {v3}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 33
    .line 34
    .line 35
    move-result-object v4

    .line 36
    check-cast v4, Landroidx/appcompat/widget/y$a;

    .line 37
    .line 38
    if-eqz v1, :cond_0

    .line 39
    .line 40
    invoke-virtual {v3}, Landroid/view/View;->getRight()I

    .line 41
    .line 42
    .line 43
    move-result v3

    .line 44
    iget v4, v4, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    .line 45
    .line 46
    add-int/2addr v3, v4

    .line 47
    goto :goto_1

    .line 48
    :cond_0
    invoke-virtual {v3}, Landroid/view/View;->getLeft()I

    .line 49
    .line 50
    .line 51
    move-result v3

    .line 52
    iget v4, v4, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    .line 53
    .line 54
    sub-int/2addr v3, v4

    .line 55
    iget v4, p0, Landroidx/appcompat/widget/y;->l:I

    .line 56
    .line 57
    sub-int/2addr v3, v4

    .line 58
    :goto_1
    invoke-virtual {p0, p1, v3}, Landroidx/appcompat/widget/y;->e(Landroid/graphics/Canvas;I)V

    .line 59
    .line 60
    .line 61
    :cond_1
    add-int/lit8 v2, v2, 0x1

    .line 62
    .line 63
    goto :goto_0

    .line 64
    :cond_2
    invoke-virtual {p0, v0}, Landroidx/appcompat/widget/y;->o(I)Z

    .line 65
    .line 66
    .line 67
    move-result v2

    .line 68
    if-eqz v2, :cond_6

    .line 69
    .line 70
    add-int/lit8 v0, v0, -0x1

    .line 71
    .line 72
    invoke-virtual {p0, v0}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    .line 73
    .line 74
    .line 75
    move-result-object v0

    .line 76
    if-nez v0, :cond_4

    .line 77
    .line 78
    if-eqz v1, :cond_3

    .line 79
    .line 80
    invoke-virtual {p0}, Landroid/view/View;->getPaddingLeft()I

    .line 81
    .line 82
    .line 83
    move-result v0

    .line 84
    goto :goto_3

    .line 85
    :cond_3
    invoke-virtual {p0}, Landroid/view/View;->getWidth()I

    .line 86
    .line 87
    .line 88
    move-result v0

    .line 89
    invoke-virtual {p0}, Landroid/view/View;->getPaddingRight()I

    .line 90
    .line 91
    .line 92
    move-result v1

    .line 93
    sub-int/2addr v0, v1

    .line 94
    iget v1, p0, Landroidx/appcompat/widget/y;->l:I

    .line 95
    .line 96
    :goto_2
    sub-int/2addr v0, v1

    .line 97
    goto :goto_3

    .line 98
    :cond_4
    invoke-virtual {v0}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 99
    .line 100
    .line 101
    move-result-object v2

    .line 102
    check-cast v2, Landroidx/appcompat/widget/y$a;

    .line 103
    .line 104
    if-eqz v1, :cond_5

    .line 105
    .line 106
    invoke-virtual {v0}, Landroid/view/View;->getLeft()I

    .line 107
    .line 108
    .line 109
    move-result v0

    .line 110
    iget v1, v2, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    .line 111
    .line 112
    sub-int/2addr v0, v1

    .line 113
    iget v1, p0, Landroidx/appcompat/widget/y;->l:I

    .line 114
    .line 115
    goto :goto_2

    .line 116
    :cond_5
    invoke-virtual {v0}, Landroid/view/View;->getRight()I

    .line 117
    .line 118
    .line 119
    move-result v0

    .line 120
    iget v1, v2, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    .line 121
    .line 122
    add-int/2addr v0, v1

    .line 123
    :goto_3
    invoke-virtual {p0, p1, v0}, Landroidx/appcompat/widget/y;->e(Landroid/graphics/Canvas;I)V

    .line 124
    .line 125
    .line 126
    :cond_6
    return-void
.end method

.method c(Landroid/graphics/Canvas;)V
    .locals 5

    .line 1
    invoke-virtual {p0}, Landroidx/appcompat/widget/y;->getVirtualChildCount()I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    const/4 v1, 0x0

    .line 6
    :goto_0
    if-ge v1, v0, :cond_1

    .line 7
    .line 8
    invoke-virtual {p0, v1}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    .line 9
    .line 10
    .line 11
    move-result-object v2

    .line 12
    if-eqz v2, :cond_0

    .line 13
    .line 14
    invoke-virtual {v2}, Landroid/view/View;->getVisibility()I

    .line 15
    .line 16
    .line 17
    move-result v3

    .line 18
    const/16 v4, 0x8

    .line 19
    .line 20
    if-eq v3, v4, :cond_0

    .line 21
    .line 22
    invoke-virtual {p0, v1}, Landroidx/appcompat/widget/y;->o(I)Z

    .line 23
    .line 24
    .line 25
    move-result v3

    .line 26
    if-eqz v3, :cond_0

    .line 27
    .line 28
    invoke-virtual {v2}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 29
    .line 30
    .line 31
    move-result-object v3

    .line 32
    check-cast v3, Landroidx/appcompat/widget/y$a;

    .line 33
    .line 34
    invoke-virtual {v2}, Landroid/view/View;->getTop()I

    .line 35
    .line 36
    .line 37
    move-result v2

    .line 38
    iget v3, v3, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    .line 39
    .line 40
    sub-int/2addr v2, v3

    .line 41
    iget v3, p0, Landroidx/appcompat/widget/y;->m:I

    .line 42
    .line 43
    sub-int/2addr v2, v3

    .line 44
    invoke-virtual {p0, p1, v2}, Landroidx/appcompat/widget/y;->d(Landroid/graphics/Canvas;I)V

    .line 45
    .line 46
    .line 47
    :cond_0
    add-int/lit8 v1, v1, 0x1

    .line 48
    .line 49
    goto :goto_0

    .line 50
    :cond_1
    invoke-virtual {p0, v0}, Landroidx/appcompat/widget/y;->o(I)Z

    .line 51
    .line 52
    .line 53
    move-result v1

    .line 54
    if-eqz v1, :cond_3

    .line 55
    .line 56
    add-int/lit8 v0, v0, -0x1

    .line 57
    .line 58
    invoke-virtual {p0, v0}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    .line 59
    .line 60
    .line 61
    move-result-object v0

    .line 62
    if-nez v0, :cond_2

    .line 63
    .line 64
    invoke-virtual {p0}, Landroid/view/View;->getHeight()I

    .line 65
    .line 66
    .line 67
    move-result v0

    .line 68
    invoke-virtual {p0}, Landroid/view/View;->getPaddingBottom()I

    .line 69
    .line 70
    .line 71
    move-result v1

    .line 72
    sub-int/2addr v0, v1

    .line 73
    iget v1, p0, Landroidx/appcompat/widget/y;->m:I

    .line 74
    .line 75
    sub-int/2addr v0, v1

    .line 76
    goto :goto_1

    .line 77
    :cond_2
    invoke-virtual {v0}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 78
    .line 79
    .line 80
    move-result-object v1

    .line 81
    check-cast v1, Landroidx/appcompat/widget/y$a;

    .line 82
    .line 83
    invoke-virtual {v0}, Landroid/view/View;->getBottom()I

    .line 84
    .line 85
    .line 86
    move-result v0

    .line 87
    iget v1, v1, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    .line 88
    .line 89
    add-int/2addr v0, v1

    .line 90
    :goto_1
    invoke-virtual {p0, p1, v0}, Landroidx/appcompat/widget/y;->d(Landroid/graphics/Canvas;I)V

    .line 91
    .line 92
    .line 93
    :cond_3
    return-void
.end method

.method protected checkLayoutParams(Landroid/view/ViewGroup$LayoutParams;)Z
    .locals 0

    .line 1
    instance-of p1, p1, Landroidx/appcompat/widget/y$a;

    .line 2
    .line 3
    return p1
.end method

.method d(Landroid/graphics/Canvas;I)V
    .locals 4

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/y;->k:Landroid/graphics/drawable/Drawable;

    .line 2
    .line 3
    invoke-virtual {p0}, Landroid/view/View;->getPaddingLeft()I

    .line 4
    .line 5
    .line 6
    move-result v1

    .line 7
    iget v2, p0, Landroidx/appcompat/widget/y;->o:I

    .line 8
    .line 9
    add-int/2addr v1, v2

    .line 10
    invoke-virtual {p0}, Landroid/view/View;->getWidth()I

    .line 11
    .line 12
    .line 13
    move-result v2

    .line 14
    invoke-virtual {p0}, Landroid/view/View;->getPaddingRight()I

    .line 15
    .line 16
    .line 17
    move-result v3

    .line 18
    sub-int/2addr v2, v3

    .line 19
    iget v3, p0, Landroidx/appcompat/widget/y;->o:I

    .line 20
    .line 21
    sub-int/2addr v2, v3

    .line 22
    iget v3, p0, Landroidx/appcompat/widget/y;->m:I

    .line 23
    .line 24
    add-int/2addr v3, p2

    .line 25
    invoke-virtual {v0, v1, p2, v2, v3}, Landroid/graphics/drawable/Drawable;->setBounds(IIII)V

    .line 26
    .line 27
    .line 28
    iget-object p2, p0, Landroidx/appcompat/widget/y;->k:Landroid/graphics/drawable/Drawable;

    .line 29
    .line 30
    invoke-virtual {p2, p1}, Landroid/graphics/drawable/Drawable;->draw(Landroid/graphics/Canvas;)V

    .line 31
    .line 32
    .line 33
    return-void
.end method

.method e(Landroid/graphics/Canvas;I)V
    .locals 5

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/y;->k:Landroid/graphics/drawable/Drawable;

    .line 2
    .line 3
    invoke-virtual {p0}, Landroid/view/View;->getPaddingTop()I

    .line 4
    .line 5
    .line 6
    move-result v1

    .line 7
    iget v2, p0, Landroidx/appcompat/widget/y;->o:I

    .line 8
    .line 9
    add-int/2addr v1, v2

    .line 10
    iget v2, p0, Landroidx/appcompat/widget/y;->l:I

    .line 11
    .line 12
    add-int/2addr v2, p2

    .line 13
    invoke-virtual {p0}, Landroid/view/View;->getHeight()I

    .line 14
    .line 15
    .line 16
    move-result v3

    .line 17
    invoke-virtual {p0}, Landroid/view/View;->getPaddingBottom()I

    .line 18
    .line 19
    .line 20
    move-result v4

    .line 21
    sub-int/2addr v3, v4

    .line 22
    iget v4, p0, Landroidx/appcompat/widget/y;->o:I

    .line 23
    .line 24
    sub-int/2addr v3, v4

    .line 25
    invoke-virtual {v0, p2, v1, v2, v3}, Landroid/graphics/drawable/Drawable;->setBounds(IIII)V

    .line 26
    .line 27
    .line 28
    iget-object p2, p0, Landroidx/appcompat/widget/y;->k:Landroid/graphics/drawable/Drawable;

    .line 29
    .line 30
    invoke-virtual {p2, p1}, Landroid/graphics/drawable/Drawable;->draw(Landroid/graphics/Canvas;)V

    .line 31
    .line 32
    .line 33
    return-void
.end method

.method protected bridge synthetic generateDefaultLayoutParams()Landroid/view/ViewGroup$LayoutParams;
    .locals 1

    .line 1
    invoke-virtual {p0}, Landroidx/appcompat/widget/y;->h()Landroidx/appcompat/widget/y$a;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    return-object v0
.end method

.method public bridge synthetic generateLayoutParams(Landroid/util/AttributeSet;)Landroid/view/ViewGroup$LayoutParams;
    .locals 0

    .line 1
    invoke-virtual {p0, p1}, Landroidx/appcompat/widget/y;->i(Landroid/util/AttributeSet;)Landroidx/appcompat/widget/y$a;

    move-result-object p1

    return-object p1
.end method

.method protected bridge synthetic generateLayoutParams(Landroid/view/ViewGroup$LayoutParams;)Landroid/view/ViewGroup$LayoutParams;
    .locals 0

    .line 2
    invoke-virtual {p0, p1}, Landroidx/appcompat/widget/y;->j(Landroid/view/ViewGroup$LayoutParams;)Landroidx/appcompat/widget/y$a;

    move-result-object p1

    return-object p1
.end method

.method public getBaseline()I
    .locals 5

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->b:I

    .line 2
    .line 3
    if-gez v0, :cond_0

    .line 4
    .line 5
    invoke-super {p0}, Landroid/view/View;->getBaseline()I

    .line 6
    .line 7
    .line 8
    move-result v0

    .line 9
    return v0

    .line 10
    :cond_0
    invoke-virtual {p0}, Landroid/view/ViewGroup;->getChildCount()I

    .line 11
    .line 12
    .line 13
    move-result v0

    .line 14
    iget v1, p0, Landroidx/appcompat/widget/y;->b:I

    .line 15
    .line 16
    if-le v0, v1, :cond_6

    .line 17
    .line 18
    invoke-virtual {p0, v1}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    .line 19
    .line 20
    .line 21
    move-result-object v0

    .line 22
    invoke-virtual {v0}, Landroid/view/View;->getBaseline()I

    .line 23
    .line 24
    .line 25
    move-result v1

    .line 26
    const/4 v2, -0x1

    .line 27
    if-ne v1, v2, :cond_2

    .line 28
    .line 29
    iget v0, p0, Landroidx/appcompat/widget/y;->b:I

    .line 30
    .line 31
    if-nez v0, :cond_1

    .line 32
    .line 33
    return v2

    .line 34
    :cond_1
    new-instance v0, Ljava/lang/RuntimeException;

    .line 35
    .line 36
    const-string v1, "mBaselineAlignedChildIndex of LinearLayout points to a View that doesn\'t know how to get its baseline."

    .line 37
    .line 38
    invoke-direct {v0, v1}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/String;)V

    .line 39
    .line 40
    .line 41
    throw v0

    .line 42
    :cond_2
    iget v2, p0, Landroidx/appcompat/widget/y;->c:I

    .line 43
    .line 44
    iget v3, p0, Landroidx/appcompat/widget/y;->d:I

    .line 45
    .line 46
    const/4 v4, 0x1

    .line 47
    if-ne v3, v4, :cond_5

    .line 48
    .line 49
    iget v3, p0, Landroidx/appcompat/widget/y;->e:I

    .line 50
    .line 51
    and-int/lit8 v3, v3, 0x70

    .line 52
    .line 53
    const/16 v4, 0x30

    .line 54
    .line 55
    if-eq v3, v4, :cond_5

    .line 56
    .line 57
    const/16 v4, 0x10

    .line 58
    .line 59
    if-eq v3, v4, :cond_4

    .line 60
    .line 61
    const/16 v4, 0x50

    .line 62
    .line 63
    if-eq v3, v4, :cond_3

    .line 64
    .line 65
    goto :goto_0

    .line 66
    :cond_3
    invoke-virtual {p0}, Landroid/view/View;->getBottom()I

    .line 67
    .line 68
    .line 69
    move-result v2

    .line 70
    invoke-virtual {p0}, Landroid/view/View;->getTop()I

    .line 71
    .line 72
    .line 73
    move-result v3

    .line 74
    sub-int/2addr v2, v3

    .line 75
    invoke-virtual {p0}, Landroid/view/View;->getPaddingBottom()I

    .line 76
    .line 77
    .line 78
    move-result v3

    .line 79
    sub-int/2addr v2, v3

    .line 80
    iget v3, p0, Landroidx/appcompat/widget/y;->f:I

    .line 81
    .line 82
    sub-int/2addr v2, v3

    .line 83
    goto :goto_0

    .line 84
    :cond_4
    invoke-virtual {p0}, Landroid/view/View;->getBottom()I

    .line 85
    .line 86
    .line 87
    move-result v3

    .line 88
    invoke-virtual {p0}, Landroid/view/View;->getTop()I

    .line 89
    .line 90
    .line 91
    move-result v4

    .line 92
    sub-int/2addr v3, v4

    .line 93
    invoke-virtual {p0}, Landroid/view/View;->getPaddingTop()I

    .line 94
    .line 95
    .line 96
    move-result v4

    .line 97
    sub-int/2addr v3, v4

    .line 98
    invoke-virtual {p0}, Landroid/view/View;->getPaddingBottom()I

    .line 99
    .line 100
    .line 101
    move-result v4

    .line 102
    sub-int/2addr v3, v4

    .line 103
    iget v4, p0, Landroidx/appcompat/widget/y;->f:I

    .line 104
    .line 105
    sub-int/2addr v3, v4

    .line 106
    div-int/lit8 v3, v3, 0x2

    .line 107
    .line 108
    add-int/2addr v2, v3

    .line 109
    :cond_5
    :goto_0
    invoke-virtual {v0}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 110
    .line 111
    .line 112
    move-result-object v0

    .line 113
    check-cast v0, Landroidx/appcompat/widget/y$a;

    .line 114
    .line 115
    iget v0, v0, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    .line 116
    .line 117
    add-int/2addr v2, v0

    .line 118
    add-int/2addr v2, v1

    .line 119
    return v2

    .line 120
    :cond_6
    new-instance v0, Ljava/lang/RuntimeException;

    .line 121
    .line 122
    const-string v1, "mBaselineAlignedChildIndex of LinearLayout set to an index that is out of bounds."

    .line 123
    .line 124
    invoke-direct {v0, v1}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/String;)V

    .line 125
    .line 126
    .line 127
    throw v0
.end method

.method public getBaselineAlignedChildIndex()I
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->b:I

    .line 2
    .line 3
    return v0
.end method

.method public getDividerDrawable()Landroid/graphics/drawable/Drawable;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/y;->k:Landroid/graphics/drawable/Drawable;

    .line 2
    .line 3
    return-object v0
.end method

.method public getDividerPadding()I
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->o:I

    .line 2
    .line 3
    return v0
.end method

.method public getDividerWidth()I
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->l:I

    .line 2
    .line 3
    return v0
.end method

.method public getGravity()I
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->e:I

    .line 2
    .line 3
    return v0
.end method

.method public getOrientation()I
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->d:I

    .line 2
    .line 3
    return v0
.end method

.method public getShowDividers()I
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->n:I

    .line 2
    .line 3
    return v0
.end method

.method getVirtualChildCount()I
    .locals 1

    .line 1
    invoke-virtual {p0}, Landroid/view/ViewGroup;->getChildCount()I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    return v0
.end method

.method public getWeightSum()F
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->g:F

    .line 2
    .line 3
    return v0
.end method

.method protected h()Landroidx/appcompat/widget/y$a;
    .locals 3

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->d:I

    .line 2
    .line 3
    const/4 v1, -0x2

    .line 4
    if-nez v0, :cond_0

    .line 5
    .line 6
    new-instance v0, Landroidx/appcompat/widget/y$a;

    .line 7
    .line 8
    invoke-direct {v0, v1, v1}, Landroidx/appcompat/widget/y$a;-><init>(II)V

    .line 9
    .line 10
    .line 11
    return-object v0

    .line 12
    :cond_0
    const/4 v2, 0x1

    .line 13
    if-ne v0, v2, :cond_1

    .line 14
    .line 15
    new-instance v0, Landroidx/appcompat/widget/y$a;

    .line 16
    .line 17
    const/4 v2, -0x1

    .line 18
    invoke-direct {v0, v2, v1}, Landroidx/appcompat/widget/y$a;-><init>(II)V

    .line 19
    .line 20
    .line 21
    return-object v0

    .line 22
    :cond_1
    const/4 v0, 0x0

    .line 23
    return-object v0
.end method

.method public i(Landroid/util/AttributeSet;)Landroidx/appcompat/widget/y$a;
    .locals 2

    .line 1
    new-instance v0, Landroidx/appcompat/widget/y$a;

    .line 2
    .line 3
    invoke-virtual {p0}, Landroid/view/View;->getContext()Landroid/content/Context;

    .line 4
    .line 5
    .line 6
    move-result-object v1

    .line 7
    invoke-direct {v0, v1, p1}, Landroidx/appcompat/widget/y$a;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;)V

    .line 8
    .line 9
    .line 10
    return-object v0
.end method

.method protected j(Landroid/view/ViewGroup$LayoutParams;)Landroidx/appcompat/widget/y$a;
    .locals 1

    .line 1
    instance-of v0, p1, Landroidx/appcompat/widget/y$a;

    .line 2
    .line 3
    if-eqz v0, :cond_0

    .line 4
    .line 5
    new-instance v0, Landroidx/appcompat/widget/y$a;

    .line 6
    .line 7
    check-cast p1, Landroidx/appcompat/widget/y$a;

    .line 8
    .line 9
    invoke-direct {v0, p1}, Landroidx/appcompat/widget/y$a;-><init>(Landroid/view/ViewGroup$MarginLayoutParams;)V

    .line 10
    .line 11
    .line 12
    return-object v0

    .line 13
    :cond_0
    instance-of v0, p1, Landroid/view/ViewGroup$MarginLayoutParams;

    .line 14
    .line 15
    if-eqz v0, :cond_1

    .line 16
    .line 17
    new-instance v0, Landroidx/appcompat/widget/y$a;

    .line 18
    .line 19
    check-cast p1, Landroid/view/ViewGroup$MarginLayoutParams;

    .line 20
    .line 21
    invoke-direct {v0, p1}, Landroidx/appcompat/widget/y$a;-><init>(Landroid/view/ViewGroup$MarginLayoutParams;)V

    .line 22
    .line 23
    .line 24
    return-object v0

    .line 25
    :cond_1
    new-instance v0, Landroidx/appcompat/widget/y$a;

    .line 26
    .line 27
    invoke-direct {v0, p1}, Landroidx/appcompat/widget/y$a;-><init>(Landroid/view/ViewGroup$LayoutParams;)V

    .line 28
    .line 29
    .line 30
    return-object v0
.end method

.method k(Landroid/view/View;I)I
    .locals 0

    .line 1
    const/4 p1, 0x0

    return p1
.end method

.method l(Landroid/view/View;)I
    .locals 0

    .line 1
    const/4 p1, 0x0

    return p1
.end method

.method m(Landroid/view/View;)I
    .locals 0

    .line 1
    const/4 p1, 0x0

    return p1
.end method

.method n(I)Landroid/view/View;
    .locals 0

    .line 1
    invoke-virtual {p0, p1}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    .line 2
    .line 3
    .line 4
    move-result-object p1

    .line 5
    return-object p1
.end method

.method protected o(I)Z
    .locals 4

    .line 1
    const/4 v0, 0x0

    .line 2
    const/4 v1, 0x1

    .line 3
    if-nez p1, :cond_1

    .line 4
    .line 5
    iget p1, p0, Landroidx/appcompat/widget/y;->n:I

    .line 6
    .line 7
    and-int/2addr p1, v1

    .line 8
    if-eqz p1, :cond_0

    .line 9
    .line 10
    return v1

    .line 11
    :cond_0
    return v0

    .line 12
    :cond_1
    invoke-virtual {p0}, Landroid/view/ViewGroup;->getChildCount()I

    .line 13
    .line 14
    .line 15
    move-result v2

    .line 16
    if-ne p1, v2, :cond_3

    .line 17
    .line 18
    iget p1, p0, Landroidx/appcompat/widget/y;->n:I

    .line 19
    .line 20
    and-int/lit8 p1, p1, 0x4

    .line 21
    .line 22
    if-eqz p1, :cond_2

    .line 23
    .line 24
    return v1

    .line 25
    :cond_2
    return v0

    .line 26
    :cond_3
    iget v2, p0, Landroidx/appcompat/widget/y;->n:I

    .line 27
    .line 28
    and-int/lit8 v2, v2, 0x2

    .line 29
    .line 30
    if-eqz v2, :cond_5

    .line 31
    .line 32
    sub-int/2addr p1, v1

    .line 33
    :goto_0
    if-ltz p1, :cond_5

    .line 34
    .line 35
    invoke-virtual {p0, p1}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    .line 36
    .line 37
    .line 38
    move-result-object v2

    .line 39
    invoke-virtual {v2}, Landroid/view/View;->getVisibility()I

    .line 40
    .line 41
    .line 42
    move-result v2

    .line 43
    const/16 v3, 0x8

    .line 44
    .line 45
    if-eq v2, v3, :cond_4

    .line 46
    .line 47
    return v1

    .line 48
    :cond_4
    add-int/lit8 p1, p1, -0x1

    .line 49
    .line 50
    goto :goto_0

    .line 51
    :cond_5
    return v0
.end method

.method protected onDraw(Landroid/graphics/Canvas;)V
    .locals 2

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/y;->k:Landroid/graphics/drawable/Drawable;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iget v0, p0, Landroidx/appcompat/widget/y;->d:I

    .line 7
    .line 8
    const/4 v1, 0x1

    .line 9
    if-ne v0, v1, :cond_1

    .line 10
    .line 11
    invoke-virtual {p0, p1}, Landroidx/appcompat/widget/y;->c(Landroid/graphics/Canvas;)V

    .line 12
    .line 13
    .line 14
    return-void

    .line 15
    :cond_1
    invoke-virtual {p0, p1}, Landroidx/appcompat/widget/y;->b(Landroid/graphics/Canvas;)V

    .line 16
    .line 17
    .line 18
    return-void
.end method

.method public onInitializeAccessibilityEvent(Landroid/view/accessibility/AccessibilityEvent;)V
    .locals 1

    .line 1
    invoke-super {p0, p1}, Landroid/view/View;->onInitializeAccessibilityEvent(Landroid/view/accessibility/AccessibilityEvent;)V

    .line 2
    .line 3
    .line 4
    const-string v0, "androidx.appcompat.widget.LinearLayoutCompat"

    .line 5
    .line 6
    invoke-virtual {p1, v0}, Landroid/view/accessibility/AccessibilityRecord;->setClassName(Ljava/lang/CharSequence;)V

    .line 7
    .line 8
    .line 9
    return-void
.end method

.method public onInitializeAccessibilityNodeInfo(Landroid/view/accessibility/AccessibilityNodeInfo;)V
    .locals 1

    .line 1
    invoke-super {p0, p1}, Landroid/view/View;->onInitializeAccessibilityNodeInfo(Landroid/view/accessibility/AccessibilityNodeInfo;)V

    .line 2
    .line 3
    .line 4
    const-string v0, "androidx.appcompat.widget.LinearLayoutCompat"

    .line 5
    .line 6
    invoke-virtual {p1, v0}, Landroid/view/accessibility/AccessibilityNodeInfo;->setClassName(Ljava/lang/CharSequence;)V

    .line 7
    .line 8
    .line 9
    return-void
.end method

.method protected onLayout(ZIIII)V
    .locals 1

    .line 1
    iget p1, p0, Landroidx/appcompat/widget/y;->d:I

    .line 2
    .line 3
    const/4 v0, 0x1

    .line 4
    if-ne p1, v0, :cond_0

    .line 5
    .line 6
    invoke-virtual {p0, p2, p3, p4, p5}, Landroidx/appcompat/widget/y;->q(IIII)V

    .line 7
    .line 8
    .line 9
    return-void

    .line 10
    :cond_0
    invoke-virtual {p0, p2, p3, p4, p5}, Landroidx/appcompat/widget/y;->p(IIII)V

    .line 11
    .line 12
    .line 13
    return-void
.end method

.method protected onMeasure(II)V
    .locals 2

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->d:I

    .line 2
    .line 3
    const/4 v1, 0x1

    .line 4
    if-ne v0, v1, :cond_0

    .line 5
    .line 6
    invoke-virtual {p0, p1, p2}, Landroidx/appcompat/widget/y;->u(II)V

    .line 7
    .line 8
    .line 9
    return-void

    .line 10
    :cond_0
    invoke-virtual {p0, p1, p2}, Landroidx/appcompat/widget/y;->s(II)V

    .line 11
    .line 12
    .line 13
    return-void
.end method

.method p(IIII)V
    .locals 21

    .line 1
    move-object/from16 v0, p0

    .line 2
    .line 3
    invoke-static {v0}, Landroidx/appcompat/widget/W;->a(Landroid/view/View;)Z

    .line 4
    .line 5
    .line 6
    move-result v1

    .line 7
    invoke-virtual {v0}, Landroid/view/View;->getPaddingTop()I

    .line 8
    .line 9
    .line 10
    move-result v6

    .line 11
    sub-int v2, p4, p2

    .line 12
    .line 13
    invoke-virtual {v0}, Landroid/view/View;->getPaddingBottom()I

    .line 14
    .line 15
    .line 16
    move-result v3

    .line 17
    sub-int v7, v2, v3

    .line 18
    .line 19
    sub-int/2addr v2, v6

    .line 20
    invoke-virtual {v0}, Landroid/view/View;->getPaddingBottom()I

    .line 21
    .line 22
    .line 23
    move-result v3

    .line 24
    sub-int v8, v2, v3

    .line 25
    .line 26
    invoke-virtual {v0}, Landroidx/appcompat/widget/y;->getVirtualChildCount()I

    .line 27
    .line 28
    .line 29
    move-result v9

    .line 30
    iget v2, v0, Landroidx/appcompat/widget/y;->e:I

    .line 31
    .line 32
    const v3, 0x800007

    .line 33
    .line 34
    .line 35
    and-int/2addr v3, v2

    .line 36
    and-int/lit8 v10, v2, 0x70

    .line 37
    .line 38
    iget-boolean v11, v0, Landroidx/appcompat/widget/y;->a:Z

    .line 39
    .line 40
    iget-object v12, v0, Landroidx/appcompat/widget/y;->i:[I

    .line 41
    .line 42
    iget-object v13, v0, Landroidx/appcompat/widget/y;->j:[I

    .line 43
    .line 44
    invoke-virtual {v0}, Landroid/view/View;->getLayoutDirection()I

    .line 45
    .line 46
    .line 47
    move-result v2

    .line 48
    invoke-static {v3, v2}, Landroidx/core/view/i;->a(II)I

    .line 49
    .line 50
    .line 51
    move-result v2

    .line 52
    const/4 v14, 0x2

    .line 53
    const/4 v15, 0x1

    .line 54
    if-eq v2, v15, :cond_1

    .line 55
    .line 56
    const/4 v3, 0x5

    .line 57
    if-eq v2, v3, :cond_0

    .line 58
    .line 59
    invoke-virtual {v0}, Landroid/view/View;->getPaddingLeft()I

    .line 60
    .line 61
    .line 62
    move-result v2

    .line 63
    goto :goto_0

    .line 64
    :cond_0
    invoke-virtual {v0}, Landroid/view/View;->getPaddingLeft()I

    .line 65
    .line 66
    .line 67
    move-result v2

    .line 68
    add-int v2, v2, p3

    .line 69
    .line 70
    sub-int v2, v2, p1

    .line 71
    .line 72
    iget v3, v0, Landroidx/appcompat/widget/y;->f:I

    .line 73
    .line 74
    sub-int/2addr v2, v3

    .line 75
    goto :goto_0

    .line 76
    :cond_1
    invoke-virtual {v0}, Landroid/view/View;->getPaddingLeft()I

    .line 77
    .line 78
    .line 79
    move-result v2

    .line 80
    sub-int v3, p3, p1

    .line 81
    .line 82
    iget v4, v0, Landroidx/appcompat/widget/y;->f:I

    .line 83
    .line 84
    sub-int/2addr v3, v4

    .line 85
    div-int/2addr v3, v14

    .line 86
    add-int/2addr v2, v3

    .line 87
    :goto_0
    const/4 v3, 0x0

    .line 88
    if-eqz v1, :cond_2

    .line 89
    .line 90
    add-int/lit8 v1, v9, -0x1

    .line 91
    .line 92
    move/from16 v16, v1

    .line 93
    .line 94
    const/16 v17, -0x1

    .line 95
    .line 96
    goto :goto_1

    .line 97
    :cond_2
    move/from16 v16, v3

    .line 98
    .line 99
    move/from16 v17, v15

    .line 100
    .line 101
    :goto_1
    move v1, v3

    .line 102
    :goto_2
    if-ge v1, v9, :cond_d

    .line 103
    .line 104
    mul-int v3, v17, v1

    .line 105
    .line 106
    add-int v3, v16, v3

    .line 107
    .line 108
    move v5, v1

    .line 109
    invoke-virtual {v0, v3}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    .line 110
    .line 111
    .line 112
    move-result-object v1

    .line 113
    if-nez v1, :cond_3

    .line 114
    .line 115
    invoke-virtual {v0, v3}, Landroidx/appcompat/widget/y;->t(I)I

    .line 116
    .line 117
    .line 118
    move-result v1

    .line 119
    add-int/2addr v2, v1

    .line 120
    move v1, v5

    .line 121
    move/from16 v19, v6

    .line 122
    .line 123
    move/from16 p2, v14

    .line 124
    .line 125
    move/from16 p4, v15

    .line 126
    .line 127
    goto/16 :goto_7

    .line 128
    .line 129
    :cond_3
    move/from16 p2, v14

    .line 130
    .line 131
    invoke-virtual {v1}, Landroid/view/View;->getVisibility()I

    .line 132
    .line 133
    .line 134
    move-result v14

    .line 135
    move/from16 p4, v15

    .line 136
    .line 137
    const/16 v15, 0x8

    .line 138
    .line 139
    if-eq v14, v15, :cond_c

    .line 140
    .line 141
    invoke-virtual {v1}, Landroid/view/View;->getMeasuredWidth()I

    .line 142
    .line 143
    .line 144
    move-result v14

    .line 145
    move v15, v5

    .line 146
    invoke-virtual {v1}, Landroid/view/View;->getMeasuredHeight()I

    .line 147
    .line 148
    .line 149
    move-result v5

    .line 150
    invoke-virtual {v1}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 151
    .line 152
    .line 153
    move-result-object v18

    .line 154
    move-object/from16 v4, v18

    .line 155
    .line 156
    check-cast v4, Landroidx/appcompat/widget/y$a;

    .line 157
    .line 158
    move/from16 p3, v2

    .line 159
    .line 160
    if-eqz v11, :cond_4

    .line 161
    .line 162
    iget v2, v4, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 163
    .line 164
    move/from16 v18, v5

    .line 165
    .line 166
    const/4 v5, -0x1

    .line 167
    if-eq v2, v5, :cond_5

    .line 168
    .line 169
    invoke-virtual {v1}, Landroid/view/View;->getBaseline()I

    .line 170
    .line 171
    .line 172
    move-result v5

    .line 173
    goto :goto_3

    .line 174
    :cond_4
    move/from16 v18, v5

    .line 175
    .line 176
    :cond_5
    const/4 v5, -0x1

    .line 177
    :goto_3
    iget v2, v4, Landroid/widget/LinearLayout$LayoutParams;->gravity:I

    .line 178
    .line 179
    if-gez v2, :cond_6

    .line 180
    .line 181
    move v2, v10

    .line 182
    :cond_6
    and-int/lit8 v2, v2, 0x70

    .line 183
    .line 184
    move/from16 v19, v6

    .line 185
    .line 186
    const/16 v6, 0x10

    .line 187
    .line 188
    if-eq v2, v6, :cond_9

    .line 189
    .line 190
    const/16 v6, 0x30

    .line 191
    .line 192
    if-eq v2, v6, :cond_8

    .line 193
    .line 194
    const/16 v6, 0x50

    .line 195
    .line 196
    if-eq v2, v6, :cond_7

    .line 197
    .line 198
    move/from16 v2, v19

    .line 199
    .line 200
    const/4 v6, -0x1

    .line 201
    goto :goto_5

    .line 202
    :cond_7
    sub-int v2, v7, v18

    .line 203
    .line 204
    iget v6, v4, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    .line 205
    .line 206
    sub-int/2addr v2, v6

    .line 207
    const/4 v6, -0x1

    .line 208
    if-eq v5, v6, :cond_a

    .line 209
    .line 210
    invoke-virtual {v1}, Landroid/view/View;->getMeasuredHeight()I

    .line 211
    .line 212
    .line 213
    move-result v20

    .line 214
    sub-int v20, v20, v5

    .line 215
    .line 216
    aget v5, v13, p2

    .line 217
    .line 218
    sub-int v5, v5, v20

    .line 219
    .line 220
    :goto_4
    sub-int/2addr v2, v5

    .line 221
    goto :goto_5

    .line 222
    :cond_8
    const/4 v6, -0x1

    .line 223
    iget v2, v4, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    .line 224
    .line 225
    add-int v2, v19, v2

    .line 226
    .line 227
    if-eq v5, v6, :cond_a

    .line 228
    .line 229
    aget v20, v12, p4

    .line 230
    .line 231
    sub-int v20, v20, v5

    .line 232
    .line 233
    add-int v2, v2, v20

    .line 234
    .line 235
    goto :goto_5

    .line 236
    :cond_9
    const/4 v6, -0x1

    .line 237
    sub-int v2, v8, v18

    .line 238
    .line 239
    div-int/lit8 v2, v2, 0x2

    .line 240
    .line 241
    add-int v2, v19, v2

    .line 242
    .line 243
    iget v5, v4, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    .line 244
    .line 245
    add-int/2addr v2, v5

    .line 246
    iget v5, v4, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    .line 247
    .line 248
    goto :goto_4

    .line 249
    :cond_a
    :goto_5
    invoke-virtual {v0, v3}, Landroidx/appcompat/widget/y;->o(I)Z

    .line 250
    .line 251
    .line 252
    move-result v5

    .line 253
    if-eqz v5, :cond_b

    .line 254
    .line 255
    iget v5, v0, Landroidx/appcompat/widget/y;->l:I

    .line 256
    .line 257
    add-int v5, p3, v5

    .line 258
    .line 259
    goto :goto_6

    .line 260
    :cond_b
    move/from16 v5, p3

    .line 261
    .line 262
    :goto_6
    iget v6, v4, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    .line 263
    .line 264
    add-int/2addr v6, v5

    .line 265
    invoke-virtual {v0, v1}, Landroidx/appcompat/widget/y;->l(Landroid/view/View;)I

    .line 266
    .line 267
    .line 268
    move-result v5

    .line 269
    add-int/2addr v5, v6

    .line 270
    move/from16 p3, v6

    .line 271
    .line 272
    move-object v6, v4

    .line 273
    move v4, v14

    .line 274
    move v14, v3

    .line 275
    move v3, v2

    .line 276
    move v2, v5

    .line 277
    move/from16 v5, v18

    .line 278
    .line 279
    invoke-direct/range {v0 .. v5}, Landroidx/appcompat/widget/y;->v(Landroid/view/View;IIII)V

    .line 280
    .line 281
    .line 282
    iget v2, v6, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    .line 283
    .line 284
    add-int/2addr v2, v4

    .line 285
    invoke-virtual {v0, v1}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    .line 286
    .line 287
    .line 288
    move-result v3

    .line 289
    add-int/2addr v2, v3

    .line 290
    add-int v6, p3, v2

    .line 291
    .line 292
    invoke-virtual {v0, v1, v14}, Landroidx/appcompat/widget/y;->k(Landroid/view/View;I)I

    .line 293
    .line 294
    .line 295
    move-result v1

    .line 296
    add-int/2addr v1, v15

    .line 297
    move v2, v6

    .line 298
    goto :goto_7

    .line 299
    :cond_c
    move/from16 p3, v2

    .line 300
    .line 301
    move v15, v5

    .line 302
    move/from16 v19, v6

    .line 303
    .line 304
    move v1, v15

    .line 305
    :goto_7
    add-int/lit8 v1, v1, 0x1

    .line 306
    .line 307
    move/from16 v14, p2

    .line 308
    .line 309
    move/from16 v15, p4

    .line 310
    .line 311
    move/from16 v6, v19

    .line 312
    .line 313
    goto/16 :goto_2

    .line 314
    .line 315
    :cond_d
    return-void
.end method

.method q(IIII)V
    .locals 11

    .line 1
    invoke-virtual {p0}, Landroid/view/View;->getPaddingLeft()I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    sub-int/2addr p3, p1

    .line 6
    invoke-virtual {p0}, Landroid/view/View;->getPaddingRight()I

    .line 7
    .line 8
    .line 9
    move-result p1

    .line 10
    sub-int p1, p3, p1

    .line 11
    .line 12
    sub-int/2addr p3, v0

    .line 13
    invoke-virtual {p0}, Landroid/view/View;->getPaddingRight()I

    .line 14
    .line 15
    .line 16
    move-result v1

    .line 17
    sub-int/2addr p3, v1

    .line 18
    invoke-virtual {p0}, Landroidx/appcompat/widget/y;->getVirtualChildCount()I

    .line 19
    .line 20
    .line 21
    move-result v1

    .line 22
    iget v2, p0, Landroidx/appcompat/widget/y;->e:I

    .line 23
    .line 24
    and-int/lit8 v3, v2, 0x70

    .line 25
    .line 26
    const v4, 0x800007

    .line 27
    .line 28
    .line 29
    and-int/2addr v2, v4

    .line 30
    const/16 v4, 0x10

    .line 31
    .line 32
    if-eq v3, v4, :cond_1

    .line 33
    .line 34
    const/16 v4, 0x50

    .line 35
    .line 36
    if-eq v3, v4, :cond_0

    .line 37
    .line 38
    invoke-virtual {p0}, Landroid/view/View;->getPaddingTop()I

    .line 39
    .line 40
    .line 41
    move-result p2

    .line 42
    goto :goto_0

    .line 43
    :cond_0
    invoke-virtual {p0}, Landroid/view/View;->getPaddingTop()I

    .line 44
    .line 45
    .line 46
    move-result v3

    .line 47
    add-int/2addr v3, p4

    .line 48
    sub-int/2addr v3, p2

    .line 49
    iget p2, p0, Landroidx/appcompat/widget/y;->f:I

    .line 50
    .line 51
    sub-int p2, v3, p2

    .line 52
    .line 53
    goto :goto_0

    .line 54
    :cond_1
    invoke-virtual {p0}, Landroid/view/View;->getPaddingTop()I

    .line 55
    .line 56
    .line 57
    move-result v3

    .line 58
    sub-int/2addr p4, p2

    .line 59
    iget p2, p0, Landroidx/appcompat/widget/y;->f:I

    .line 60
    .line 61
    sub-int/2addr p4, p2

    .line 62
    div-int/lit8 p4, p4, 0x2

    .line 63
    .line 64
    add-int p2, v3, p4

    .line 65
    .line 66
    :goto_0
    const/4 p4, 0x0

    .line 67
    :goto_1
    if-ge p4, v1, :cond_8

    .line 68
    .line 69
    invoke-virtual {p0, p4}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    .line 70
    .line 71
    .line 72
    move-result-object v4

    .line 73
    const/4 v9, 0x1

    .line 74
    if-nez v4, :cond_3

    .line 75
    .line 76
    invoke-virtual {p0, p4}, Landroidx/appcompat/widget/y;->t(I)I

    .line 77
    .line 78
    .line 79
    move-result v3

    .line 80
    add-int/2addr p2, v3

    .line 81
    :cond_2
    move-object v3, p0

    .line 82
    goto :goto_5

    .line 83
    :cond_3
    invoke-virtual {v4}, Landroid/view/View;->getVisibility()I

    .line 84
    .line 85
    .line 86
    move-result v3

    .line 87
    const/16 v5, 0x8

    .line 88
    .line 89
    if-eq v3, v5, :cond_2

    .line 90
    .line 91
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredWidth()I

    .line 92
    .line 93
    .line 94
    move-result v7

    .line 95
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredHeight()I

    .line 96
    .line 97
    .line 98
    move-result v8

    .line 99
    invoke-virtual {v4}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 100
    .line 101
    .line 102
    move-result-object v3

    .line 103
    move-object v10, v3

    .line 104
    check-cast v10, Landroidx/appcompat/widget/y$a;

    .line 105
    .line 106
    iget v3, v10, Landroid/widget/LinearLayout$LayoutParams;->gravity:I

    .line 107
    .line 108
    if-gez v3, :cond_4

    .line 109
    .line 110
    move v3, v2

    .line 111
    :cond_4
    invoke-virtual {p0}, Landroid/view/View;->getLayoutDirection()I

    .line 112
    .line 113
    .line 114
    move-result v5

    .line 115
    invoke-static {v3, v5}, Landroidx/core/view/i;->a(II)I

    .line 116
    .line 117
    .line 118
    move-result v3

    .line 119
    and-int/lit8 v3, v3, 0x7

    .line 120
    .line 121
    if-eq v3, v9, :cond_6

    .line 122
    .line 123
    const/4 v5, 0x5

    .line 124
    if-eq v3, v5, :cond_5

    .line 125
    .line 126
    iget v3, v10, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    .line 127
    .line 128
    add-int/2addr v3, v0

    .line 129
    :goto_2
    move v5, v3

    .line 130
    goto :goto_4

    .line 131
    :cond_5
    sub-int v3, p1, v7

    .line 132
    .line 133
    iget v5, v10, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    .line 134
    .line 135
    :goto_3
    sub-int/2addr v3, v5

    .line 136
    goto :goto_2

    .line 137
    :cond_6
    sub-int v3, p3, v7

    .line 138
    .line 139
    div-int/lit8 v3, v3, 0x2

    .line 140
    .line 141
    add-int/2addr v3, v0

    .line 142
    iget v5, v10, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    .line 143
    .line 144
    add-int/2addr v3, v5

    .line 145
    iget v5, v10, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    .line 146
    .line 147
    goto :goto_3

    .line 148
    :goto_4
    invoke-virtual {p0, p4}, Landroidx/appcompat/widget/y;->o(I)Z

    .line 149
    .line 150
    .line 151
    move-result v3

    .line 152
    if-eqz v3, :cond_7

    .line 153
    .line 154
    iget v3, p0, Landroidx/appcompat/widget/y;->m:I

    .line 155
    .line 156
    add-int/2addr p2, v3

    .line 157
    :cond_7
    iget v3, v10, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    .line 158
    .line 159
    add-int/2addr p2, v3

    .line 160
    invoke-virtual {p0, v4}, Landroidx/appcompat/widget/y;->l(Landroid/view/View;)I

    .line 161
    .line 162
    .line 163
    move-result v3

    .line 164
    add-int v6, p2, v3

    .line 165
    .line 166
    move-object v3, p0

    .line 167
    invoke-direct/range {v3 .. v8}, Landroidx/appcompat/widget/y;->v(Landroid/view/View;IIII)V

    .line 168
    .line 169
    .line 170
    iget v5, v10, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    .line 171
    .line 172
    add-int/2addr v8, v5

    .line 173
    invoke-virtual {p0, v4}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    .line 174
    .line 175
    .line 176
    move-result v5

    .line 177
    add-int/2addr v8, v5

    .line 178
    add-int/2addr p2, v8

    .line 179
    invoke-virtual {p0, v4, p4}, Landroidx/appcompat/widget/y;->k(Landroid/view/View;I)I

    .line 180
    .line 181
    .line 182
    move-result v4

    .line 183
    add-int/2addr p4, v4

    .line 184
    :goto_5
    add-int/2addr p4, v9

    .line 185
    goto :goto_1

    .line 186
    :cond_8
    move-object v3, p0

    .line 187
    return-void
.end method

.method r(Landroid/view/View;IIIII)V
    .locals 0

    .line 1
    move-object p2, p1

    .line 2
    move-object p1, p0

    .line 3
    invoke-virtual/range {p1 .. p6}, Landroid/view/ViewGroup;->measureChildWithMargins(Landroid/view/View;IIII)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method s(II)V
    .locals 38

    move-object/from16 v0, p0

    const/4 v7, 0x0

    .line 1
    iput v7, v0, Landroidx/appcompat/widget/y;->f:I

    .line 2
    invoke-virtual {v0}, Landroidx/appcompat/widget/y;->getVirtualChildCount()I

    move-result v8

    .line 3
    invoke-static/range {p1 .. p1}, Landroid/view/View$MeasureSpec;->getMode(I)I

    move-result v9

    .line 4
    invoke-static/range {p2 .. p2}, Landroid/view/View$MeasureSpec;->getMode(I)I

    move-result v10

    .line 5
    iget-object v1, v0, Landroidx/appcompat/widget/y;->i:[I

    const/4 v11, 0x4

    if-eqz v1, :cond_0

    iget-object v1, v0, Landroidx/appcompat/widget/y;->j:[I

    if-nez v1, :cond_1

    .line 6
    :cond_0
    new-array v1, v11, [I

    iput-object v1, v0, Landroidx/appcompat/widget/y;->i:[I

    .line 7
    new-array v1, v11, [I

    iput-object v1, v0, Landroidx/appcompat/widget/y;->j:[I

    .line 8
    :cond_1
    iget-object v12, v0, Landroidx/appcompat/widget/y;->i:[I

    .line 9
    iget-object v13, v0, Landroidx/appcompat/widget/y;->j:[I

    const/4 v14, 0x3

    const/4 v15, -0x1

    .line 10
    aput v15, v12, v14

    const/16 v16, 0x2

    aput v15, v12, v16

    const/16 v17, 0x1

    aput v15, v12, v17

    aput v15, v12, v7

    .line 11
    aput v15, v13, v14

    aput v15, v13, v16

    aput v15, v13, v17

    aput v15, v13, v7

    .line 12
    iget-boolean v1, v0, Landroidx/appcompat/widget/y;->a:Z

    .line 13
    iget-boolean v2, v0, Landroidx/appcompat/widget/y;->h:Z

    const/high16 v3, 0x40000000    # 2.0f

    if-ne v9, v3, :cond_2

    move/from16 v18, v17

    goto :goto_0

    :cond_2
    move/from16 v18, v7

    :goto_0
    const/16 v19, 0x0

    move v4, v2

    move v2, v7

    move v6, v2

    move v15, v6

    move/from16 v22, v15

    move/from16 v24, v22

    move/from16 v26, v24

    move/from16 v20, v11

    move/from16 v21, v14

    move/from16 v25, v17

    move/from16 v5, v19

    move/from16 v11, v26

    move v14, v11

    :goto_1
    move/from16 v27, v6

    const/16 v6, 0x8

    if-ge v2, v8, :cond_15

    move/from16 v30, v1

    .line 14
    invoke-virtual {v0, v2}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    move-result-object v1

    if-nez v1, :cond_3

    .line 15
    iget v1, v0, Landroidx/appcompat/widget/y;->f:I

    invoke-virtual {v0, v2}, Landroidx/appcompat/widget/y;->t(I)I

    move-result v6

    add-int/2addr v1, v6

    iput v1, v0, Landroidx/appcompat/widget/y;->f:I

    :goto_2
    move/from16 v3, p1

    move/from16 v1, p2

    move/from16 v34, v9

    move-object/from16 v33, v12

    move-object/from16 v28, v13

    move/from16 v6, v27

    move/from16 v27, v4

    goto/16 :goto_d

    .line 16
    :cond_3
    invoke-virtual {v1}, Landroid/view/View;->getVisibility()I

    move-result v7

    if-ne v7, v6, :cond_4

    .line 17
    invoke-virtual {v0, v1, v2}, Landroidx/appcompat/widget/y;->k(Landroid/view/View;I)I

    move-result v1

    add-int/2addr v2, v1

    goto :goto_2

    .line 18
    :cond_4
    invoke-virtual {v0, v2}, Landroidx/appcompat/widget/y;->o(I)Z

    move-result v6

    if-eqz v6, :cond_5

    .line 19
    iget v6, v0, Landroidx/appcompat/widget/y;->f:I

    iget v7, v0, Landroidx/appcompat/widget/y;->l:I

    add-int/2addr v6, v7

    iput v6, v0, Landroidx/appcompat/widget/y;->f:I

    .line 20
    :cond_5
    invoke-virtual {v1}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v6

    move-object v7, v6

    check-cast v7, Landroidx/appcompat/widget/y$a;

    .line 21
    iget v6, v7, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    add-float v32, v5, v6

    if-ne v9, v3, :cond_8

    .line 22
    iget v5, v7, Landroid/widget/LinearLayout$LayoutParams;->width:I

    if-nez v5, :cond_8

    cmpl-float v5, v6, v19

    if-lez v5, :cond_8

    if-eqz v18, :cond_6

    .line 23
    iget v5, v0, Landroidx/appcompat/widget/y;->f:I

    iget v6, v7, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    iget v3, v7, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v6, v3

    add-int/2addr v5, v6

    iput v5, v0, Landroidx/appcompat/widget/y;->f:I

    goto :goto_3

    .line 24
    :cond_6
    iget v3, v0, Landroidx/appcompat/widget/y;->f:I

    .line 25
    iget v5, v7, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    add-int/2addr v5, v3

    iget v6, v7, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v5, v6

    invoke-static {v3, v5}, Ljava/lang/Math;->max(II)I

    move-result v3

    iput v3, v0, Landroidx/appcompat/widget/y;->f:I

    :goto_3
    if-eqz v30, :cond_7

    const/4 v3, 0x0

    .line 26
    invoke-static {v3, v3}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v5

    .line 27
    invoke-virtual {v1, v5, v5}, Landroid/view/View;->measure(II)V

    move/from16 v3, p1

    move/from16 v34, v9

    move-object/from16 v33, v12

    move-object/from16 v28, v13

    move/from16 v12, v27

    const/16 v29, -0x2

    move/from16 v27, v4

    move-object v4, v1

    move/from16 v1, p2

    goto/16 :goto_7

    :cond_7
    move/from16 v3, p1

    move/from16 v34, v9

    move-object/from16 v33, v12

    move-object/from16 v28, v13

    move/from16 v22, v17

    move/from16 v12, v27

    const/high16 v5, 0x40000000    # 2.0f

    const/16 v29, -0x2

    move/from16 v27, v4

    move-object v4, v1

    move/from16 v1, p2

    goto/16 :goto_8

    .line 28
    :cond_8
    iget v3, v7, Landroid/widget/LinearLayout$LayoutParams;->width:I

    if-nez v3, :cond_9

    cmpl-float v3, v6, v19

    if-lez v3, :cond_9

    const/4 v3, -0x2

    .line 29
    iput v3, v7, Landroid/widget/LinearLayout$LayoutParams;->width:I

    const/4 v5, 0x0

    goto :goto_4

    :cond_9
    const/4 v3, -0x2

    const/high16 v5, -0x80000000

    :goto_4
    cmpl-float v6, v32, v19

    if-nez v6, :cond_a

    .line 30
    iget v6, v0, Landroidx/appcompat/widget/y;->f:I

    move/from16 v37, v6

    move v6, v4

    move/from16 v4, v37

    goto :goto_5

    :cond_a
    move v6, v4

    const/4 v4, 0x0

    :goto_5
    const/16 v28, 0x0

    move/from16 v29, v3

    move/from16 v34, v9

    move-object/from16 v33, v12

    move/from16 v12, v27

    move/from16 v3, p1

    move v9, v5

    move/from16 v27, v6

    move/from16 v6, v28

    move/from16 v5, p2

    move-object/from16 v28, v13

    const/high16 v13, -0x80000000

    .line 31
    invoke-virtual/range {v0 .. v6}, Landroidx/appcompat/widget/y;->r(Landroid/view/View;IIIII)V

    move-object v4, v1

    move v1, v5

    if-eq v9, v13, :cond_b

    .line 32
    iput v9, v7, Landroid/widget/LinearLayout$LayoutParams;->width:I

    .line 33
    :cond_b
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredWidth()I

    move-result v5

    if-eqz v18, :cond_c

    .line 34
    iget v6, v0, Landroidx/appcompat/widget/y;->f:I

    iget v9, v7, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    add-int/2addr v9, v5

    iget v13, v7, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v9, v13

    .line 35
    invoke-virtual {v0, v4}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    move-result v13

    add-int/2addr v9, v13

    add-int/2addr v6, v9

    iput v6, v0, Landroidx/appcompat/widget/y;->f:I

    goto :goto_6

    .line 36
    :cond_c
    iget v6, v0, Landroidx/appcompat/widget/y;->f:I

    add-int v9, v6, v5

    .line 37
    iget v13, v7, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    add-int/2addr v9, v13

    iget v13, v7, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v9, v13

    .line 38
    invoke-virtual {v0, v4}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    move-result v13

    add-int/2addr v9, v13

    .line 39
    invoke-static {v6, v9}, Ljava/lang/Math;->max(II)I

    move-result v6

    iput v6, v0, Landroidx/appcompat/widget/y;->f:I

    :goto_6
    if-eqz v27, :cond_d

    .line 40
    invoke-static {v5, v15}, Ljava/lang/Math;->max(II)I

    move-result v15

    :cond_d
    :goto_7
    const/high16 v5, 0x40000000    # 2.0f

    :goto_8
    if-eq v10, v5, :cond_e

    .line 41
    iget v5, v7, Landroid/widget/LinearLayout$LayoutParams;->height:I

    const/4 v6, -0x1

    if-ne v5, v6, :cond_e

    move/from16 v5, v17

    move/from16 v26, v5

    goto :goto_9

    :cond_e
    const/4 v5, 0x0

    .line 42
    :goto_9
    iget v6, v7, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    iget v9, v7, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    add-int/2addr v6, v9

    .line 43
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredHeight()I

    move-result v9

    add-int/2addr v9, v6

    .line 44
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredState()I

    move-result v13

    move/from16 v35, v6

    move/from16 v6, v24

    invoke-static {v6, v13}, Landroid/view/View;->combineMeasuredStates(II)I

    move-result v24

    if-eqz v30, :cond_10

    .line 45
    invoke-virtual {v4}, Landroid/view/View;->getBaseline()I

    move-result v6

    const/4 v13, -0x1

    if-eq v6, v13, :cond_10

    .line 46
    iget v13, v7, Landroid/widget/LinearLayout$LayoutParams;->gravity:I

    if-gez v13, :cond_f

    iget v13, v0, Landroidx/appcompat/widget/y;->e:I

    :cond_f
    and-int/lit8 v13, v13, 0x70

    shr-int/lit8 v13, v13, 0x4

    and-int/lit8 v13, v13, -0x2

    shr-int/lit8 v13, v13, 0x1

    move/from16 v36, v5

    .line 47
    aget v5, v33, v13

    invoke-static {v5, v6}, Ljava/lang/Math;->max(II)I

    move-result v5

    aput v5, v33, v13

    .line 48
    aget v5, v28, v13

    sub-int v6, v9, v6

    invoke-static {v5, v6}, Ljava/lang/Math;->max(II)I

    move-result v5

    aput v5, v28, v13

    goto :goto_a

    :cond_10
    move/from16 v36, v5

    .line 49
    :goto_a
    invoke-static {v12, v9}, Ljava/lang/Math;->max(II)I

    move-result v6

    if-eqz v25, :cond_11

    .line 50
    iget v5, v7, Landroid/widget/LinearLayout$LayoutParams;->height:I

    const/4 v13, -0x1

    if-ne v5, v13, :cond_11

    move/from16 v25, v17

    goto :goto_b

    :cond_11
    const/16 v25, 0x0

    .line 51
    :goto_b
    iget v5, v7, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    cmpl-float v5, v5, v19

    if-lez v5, :cond_13

    if-eqz v36, :cond_12

    move/from16 v9, v35

    .line 52
    :cond_12
    invoke-static {v14, v9}, Ljava/lang/Math;->max(II)I

    move-result v14

    goto :goto_c

    :cond_13
    if-eqz v36, :cond_14

    move/from16 v9, v35

    .line 53
    :cond_14
    invoke-static {v11, v9}, Ljava/lang/Math;->max(II)I

    move-result v11

    .line 54
    :goto_c
    invoke-virtual {v0, v4, v2}, Landroidx/appcompat/widget/y;->k(Landroid/view/View;I)I

    move-result v4

    add-int/2addr v2, v4

    move/from16 v5, v32

    :goto_d
    add-int/lit8 v2, v2, 0x1

    move/from16 v4, v27

    move-object/from16 v13, v28

    move/from16 v1, v30

    move-object/from16 v12, v33

    move/from16 v9, v34

    const/high16 v3, 0x40000000    # 2.0f

    const/4 v7, 0x0

    goto/16 :goto_1

    :cond_15
    move/from16 v3, p1

    move/from16 v30, v1

    move v2, v6

    move/from16 v34, v9

    move-object/from16 v33, v12

    move-object/from16 v28, v13

    move/from16 v6, v24

    move/from16 v12, v27

    const/high16 v13, -0x80000000

    const/16 v29, -0x2

    move/from16 v1, p2

    move/from16 v27, v4

    .line 55
    iget v4, v0, Landroidx/appcompat/widget/y;->f:I

    if-lez v4, :cond_16

    invoke-virtual {v0, v8}, Landroidx/appcompat/widget/y;->o(I)Z

    move-result v4

    if-eqz v4, :cond_16

    .line 56
    iget v4, v0, Landroidx/appcompat/widget/y;->f:I

    iget v7, v0, Landroidx/appcompat/widget/y;->l:I

    add-int/2addr v4, v7

    iput v4, v0, Landroidx/appcompat/widget/y;->f:I

    .line 57
    :cond_16
    aget v4, v33, v17

    const/4 v7, -0x1

    if-ne v4, v7, :cond_18

    const/16 v31, 0x0

    aget v9, v33, v31

    if-ne v9, v7, :cond_18

    aget v9, v33, v16

    if-ne v9, v7, :cond_18

    aget v9, v33, v21

    if-eq v9, v7, :cond_17

    goto :goto_e

    :cond_17
    move v2, v12

    goto :goto_f

    .line 58
    :cond_18
    :goto_e
    aget v7, v33, v21

    const/16 v31, 0x0

    aget v9, v33, v31

    aget v2, v33, v16

    .line 59
    invoke-static {v4, v2}, Ljava/lang/Math;->max(II)I

    move-result v2

    .line 60
    invoke-static {v9, v2}, Ljava/lang/Math;->max(II)I

    move-result v2

    .line 61
    invoke-static {v7, v2}, Ljava/lang/Math;->max(II)I

    move-result v2

    .line 62
    aget v4, v28, v21

    aget v7, v28, v31

    aget v9, v28, v17

    aget v13, v28, v16

    .line 63
    invoke-static {v9, v13}, Ljava/lang/Math;->max(II)I

    move-result v9

    .line 64
    invoke-static {v7, v9}, Ljava/lang/Math;->max(II)I

    move-result v7

    .line 65
    invoke-static {v4, v7}, Ljava/lang/Math;->max(II)I

    move-result v4

    add-int/2addr v2, v4

    .line 66
    invoke-static {v12, v2}, Ljava/lang/Math;->max(II)I

    move-result v2

    :goto_f
    if-eqz v27, :cond_1e

    move/from16 v4, v34

    const/high16 v13, -0x80000000

    if-eq v4, v13, :cond_19

    if-nez v4, :cond_1a

    :cond_19
    const/4 v7, 0x0

    goto :goto_11

    :cond_1a
    move/from16 v32, v2

    :goto_10
    move/from16 v34, v5

    goto/16 :goto_16

    .line 67
    :goto_11
    iput v7, v0, Landroidx/appcompat/widget/y;->f:I

    const/4 v7, 0x0

    :goto_12
    if-ge v7, v8, :cond_1a

    .line 68
    invoke-virtual {v0, v7}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    move-result-object v9

    if-nez v9, :cond_1b

    .line 69
    iget v9, v0, Landroidx/appcompat/widget/y;->f:I

    invoke-virtual {v0, v7}, Landroidx/appcompat/widget/y;->t(I)I

    move-result v12

    add-int/2addr v9, v12

    iput v9, v0, Landroidx/appcompat/widget/y;->f:I

    goto :goto_13

    .line 70
    :cond_1b
    invoke-virtual {v9}, Landroid/view/View;->getVisibility()I

    move-result v12

    const/16 v13, 0x8

    if-ne v12, v13, :cond_1c

    .line 71
    invoke-virtual {v0, v9, v7}, Landroidx/appcompat/widget/y;->k(Landroid/view/View;I)I

    move-result v9

    add-int/2addr v7, v9

    :goto_13
    move/from16 v32, v2

    :goto_14
    move/from16 v34, v5

    goto :goto_15

    .line 72
    :cond_1c
    invoke-virtual {v9}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v12

    check-cast v12, Landroidx/appcompat/widget/y$a;

    if-eqz v18, :cond_1d

    .line 73
    iget v13, v0, Landroidx/appcompat/widget/y;->f:I

    move/from16 v32, v2

    iget v2, v12, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    add-int/2addr v2, v15

    iget v12, v12, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v2, v12

    .line 74
    invoke-virtual {v0, v9}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    move-result v9

    add-int/2addr v2, v9

    add-int/2addr v13, v2

    iput v13, v0, Landroidx/appcompat/widget/y;->f:I

    goto :goto_14

    :cond_1d
    move/from16 v32, v2

    .line 75
    iget v2, v0, Landroidx/appcompat/widget/y;->f:I

    add-int v13, v2, v15

    move/from16 v34, v5

    .line 76
    iget v5, v12, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    add-int/2addr v13, v5

    iget v5, v12, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v13, v5

    .line 77
    invoke-virtual {v0, v9}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    move-result v5

    add-int/2addr v13, v5

    .line 78
    invoke-static {v2, v13}, Ljava/lang/Math;->max(II)I

    move-result v2

    iput v2, v0, Landroidx/appcompat/widget/y;->f:I

    :goto_15
    add-int/lit8 v7, v7, 0x1

    move/from16 v2, v32

    move/from16 v5, v34

    goto :goto_12

    :cond_1e
    move/from16 v32, v2

    move/from16 v4, v34

    goto :goto_10

    .line 79
    :goto_16
    iget v2, v0, Landroidx/appcompat/widget/y;->f:I

    invoke-virtual {v0}, Landroid/view/View;->getPaddingLeft()I

    move-result v5

    invoke-virtual {v0}, Landroid/view/View;->getPaddingRight()I

    move-result v7

    add-int/2addr v5, v7

    add-int/2addr v2, v5

    iput v2, v0, Landroidx/appcompat/widget/y;->f:I

    .line 80
    invoke-virtual {v0}, Landroid/view/View;->getSuggestedMinimumWidth()I

    move-result v5

    invoke-static {v2, v5}, Ljava/lang/Math;->max(II)I

    move-result v2

    const/4 v7, 0x0

    .line 81
    invoke-static {v2, v3, v7}, Landroid/view/View;->resolveSizeAndState(III)I

    move-result v2

    const v5, 0xffffff

    and-int/2addr v5, v2

    .line 82
    iget v7, v0, Landroidx/appcompat/widget/y;->f:I

    sub-int/2addr v5, v7

    if-nez v22, :cond_23

    if-eqz v5, :cond_1f

    cmpl-float v9, v34, v19

    if-lez v9, :cond_1f

    goto :goto_19

    .line 83
    :cond_1f
    invoke-static {v11, v14}, Ljava/lang/Math;->max(II)I

    move-result v5

    if-eqz v27, :cond_22

    const/high16 v9, 0x40000000    # 2.0f

    if-eq v4, v9, :cond_22

    const/4 v4, 0x0

    :goto_17
    if-ge v4, v8, :cond_22

    .line 84
    invoke-virtual {v0, v4}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    move-result-object v9

    if-eqz v9, :cond_21

    .line 85
    invoke-virtual {v9}, Landroid/view/View;->getVisibility()I

    move-result v11

    const/16 v13, 0x8

    if-ne v11, v13, :cond_20

    goto :goto_18

    .line 86
    :cond_20
    invoke-virtual {v9}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v11

    check-cast v11, Landroidx/appcompat/widget/y$a;

    .line 87
    iget v11, v11, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    cmpl-float v11, v11, v19

    if-lez v11, :cond_21

    const/high16 v11, 0x40000000    # 2.0f

    .line 88
    invoke-static {v15, v11}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v12

    .line 89
    invoke-virtual {v9}, Landroid/view/View;->getMeasuredHeight()I

    move-result v13

    invoke-static {v13, v11}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v13

    .line 90
    invoke-virtual {v9, v12, v13}, Landroid/view/View;->measure(II)V

    :cond_21
    :goto_18
    add-int/lit8 v4, v4, 0x1

    goto :goto_17

    :cond_22
    move/from16 v27, v2

    move/from16 v24, v6

    move/from16 v2, v32

    const/high16 v22, -0x1000000

    goto/16 :goto_27

    .line 91
    :cond_23
    :goto_19
    iget v9, v0, Landroidx/appcompat/widget/y;->g:F

    cmpl-float v12, v9, v19

    if-lez v12, :cond_24

    move/from16 v34, v9

    :cond_24
    const/16 v23, -0x1

    .line 92
    aput v23, v33, v21

    aput v23, v33, v16

    aput v23, v33, v17

    const/4 v9, 0x0

    aput v23, v33, v9

    .line 93
    aput v23, v28, v21

    aput v23, v28, v16

    aput v23, v28, v17

    aput v23, v28, v9

    .line 94
    iput v9, v0, Landroidx/appcompat/widget/y;->f:I

    move v9, v6

    const/4 v6, -0x1

    const/4 v12, 0x0

    :goto_1a
    if-ge v12, v8, :cond_33

    .line 95
    invoke-virtual {v0, v12}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    move-result-object v13

    if-eqz v13, :cond_25

    .line 96
    invoke-virtual {v13}, Landroid/view/View;->getVisibility()I

    move-result v14

    const/16 v15, 0x8

    if-ne v14, v15, :cond_26

    :cond_25
    move/from16 v27, v2

    const/high16 v22, -0x1000000

    goto/16 :goto_24

    .line 97
    :cond_26
    invoke-virtual {v13}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v14

    check-cast v14, Landroidx/appcompat/widget/y$a;

    const/high16 v22, -0x1000000

    .line 98
    iget v7, v14, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    cmpl-float v24, v7, v19

    if-lez v24, :cond_2b

    int-to-float v15, v5

    mul-float/2addr v15, v7

    div-float v15, v15, v34

    float-to-int v15, v15

    sub-float v34, v34, v7

    sub-int/2addr v5, v15

    .line 99
    invoke-virtual {v0}, Landroid/view/View;->getPaddingTop()I

    move-result v7

    invoke-virtual {v0}, Landroid/view/View;->getPaddingBottom()I

    move-result v27

    add-int v7, v7, v27

    move/from16 v27, v2

    iget v2, v14, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    add-int/2addr v7, v2

    iget v2, v14, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    add-int/2addr v7, v2

    iget v2, v14, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 100
    invoke-static {v1, v7, v2}, Landroid/view/ViewGroup;->getChildMeasureSpec(III)I

    move-result v2

    .line 101
    iget v7, v14, Landroid/widget/LinearLayout$LayoutParams;->width:I

    if-nez v7, :cond_29

    const/high16 v7, 0x40000000    # 2.0f

    if-eq v4, v7, :cond_27

    goto :goto_1c

    :cond_27
    if-lez v15, :cond_28

    goto :goto_1b

    :cond_28
    const/4 v15, 0x0

    .line 102
    :goto_1b
    invoke-static {v15, v7}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v15

    invoke-virtual {v13, v15, v2}, Landroid/view/View;->measure(II)V

    goto :goto_1d

    :cond_29
    const/high16 v7, 0x40000000    # 2.0f

    .line 103
    :goto_1c
    invoke-virtual {v13}, Landroid/view/View;->getMeasuredWidth()I

    move-result v32

    add-int v15, v32, v15

    if-gez v15, :cond_2a

    const/4 v15, 0x0

    .line 104
    :cond_2a
    invoke-static {v15, v7}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v15

    .line 105
    invoke-virtual {v13, v15, v2}, Landroid/view/View;->measure(II)V

    .line 106
    :goto_1d
    invoke-virtual {v13}, Landroid/view/View;->getMeasuredState()I

    move-result v2

    and-int v2, v2, v22

    .line 107
    invoke-static {v9, v2}, Landroid/view/View;->combineMeasuredStates(II)I

    move-result v9

    goto :goto_1e

    :cond_2b
    move/from16 v27, v2

    :goto_1e
    if-eqz v18, :cond_2c

    .line 108
    iget v2, v0, Landroidx/appcompat/widget/y;->f:I

    invoke-virtual {v13}, Landroid/view/View;->getMeasuredWidth()I

    move-result v7

    iget v15, v14, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    add-int/2addr v7, v15

    iget v15, v14, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v7, v15

    .line 109
    invoke-virtual {v0, v13}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    move-result v15

    add-int/2addr v7, v15

    add-int/2addr v2, v7

    iput v2, v0, Landroidx/appcompat/widget/y;->f:I

    :goto_1f
    const/high16 v7, 0x40000000    # 2.0f

    goto :goto_20

    .line 110
    :cond_2c
    iget v2, v0, Landroidx/appcompat/widget/y;->f:I

    .line 111
    invoke-virtual {v13}, Landroid/view/View;->getMeasuredWidth()I

    move-result v7

    add-int/2addr v7, v2

    iget v15, v14, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    add-int/2addr v7, v15

    iget v15, v14, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v7, v15

    .line 112
    invoke-virtual {v0, v13}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    move-result v15

    add-int/2addr v7, v15

    .line 113
    invoke-static {v2, v7}, Ljava/lang/Math;->max(II)I

    move-result v2

    iput v2, v0, Landroidx/appcompat/widget/y;->f:I

    goto :goto_1f

    :goto_20
    if-eq v10, v7, :cond_2d

    .line 114
    iget v2, v14, Landroid/widget/LinearLayout$LayoutParams;->height:I

    const/4 v7, -0x1

    if-ne v2, v7, :cond_2d

    move/from16 v2, v17

    goto :goto_21

    :cond_2d
    const/4 v2, 0x0

    .line 115
    :goto_21
    iget v7, v14, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    iget v15, v14, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    add-int/2addr v7, v15

    .line 116
    invoke-virtual {v13}, Landroid/view/View;->getMeasuredHeight()I

    move-result v15

    add-int/2addr v15, v7

    .line 117
    invoke-static {v6, v15}, Ljava/lang/Math;->max(II)I

    move-result v6

    if-eqz v2, :cond_2e

    goto :goto_22

    :cond_2e
    move v7, v15

    .line 118
    :goto_22
    invoke-static {v11, v7}, Ljava/lang/Math;->max(II)I

    move-result v2

    if-eqz v25, :cond_2f

    .line 119
    iget v7, v14, Landroid/widget/LinearLayout$LayoutParams;->height:I

    const/4 v11, -0x1

    if-ne v7, v11, :cond_30

    move/from16 v7, v17

    goto :goto_23

    :cond_2f
    const/4 v11, -0x1

    :cond_30
    const/4 v7, 0x0

    :goto_23
    if-eqz v30, :cond_32

    .line 120
    invoke-virtual {v13}, Landroid/view/View;->getBaseline()I

    move-result v13

    if-eq v13, v11, :cond_32

    .line 121
    iget v11, v14, Landroid/widget/LinearLayout$LayoutParams;->gravity:I

    if-gez v11, :cond_31

    iget v11, v0, Landroidx/appcompat/widget/y;->e:I

    :cond_31
    and-int/lit8 v11, v11, 0x70

    shr-int/lit8 v11, v11, 0x4

    and-int/lit8 v11, v11, -0x2

    shr-int/lit8 v11, v11, 0x1

    .line 122
    aget v14, v33, v11

    invoke-static {v14, v13}, Ljava/lang/Math;->max(II)I

    move-result v14

    aput v14, v33, v11

    .line 123
    aget v14, v28, v11

    sub-int/2addr v15, v13

    invoke-static {v14, v15}, Ljava/lang/Math;->max(II)I

    move-result v13

    aput v13, v28, v11

    :cond_32
    move v11, v2

    move/from16 v25, v7

    :goto_24
    add-int/lit8 v12, v12, 0x1

    move/from16 v2, v27

    goto/16 :goto_1a

    :cond_33
    move/from16 v27, v2

    const/high16 v22, -0x1000000

    .line 124
    iget v2, v0, Landroidx/appcompat/widget/y;->f:I

    invoke-virtual {v0}, Landroid/view/View;->getPaddingLeft()I

    move-result v4

    invoke-virtual {v0}, Landroid/view/View;->getPaddingRight()I

    move-result v5

    add-int/2addr v4, v5

    add-int/2addr v2, v4

    iput v2, v0, Landroidx/appcompat/widget/y;->f:I

    .line 125
    aget v2, v33, v17

    const/4 v13, -0x1

    if-ne v2, v13, :cond_35

    const/16 v31, 0x0

    aget v4, v33, v31

    if-ne v4, v13, :cond_35

    aget v4, v33, v16

    if-ne v4, v13, :cond_35

    aget v4, v33, v21

    if-eq v4, v13, :cond_34

    goto :goto_25

    :cond_34
    move v2, v6

    goto :goto_26

    .line 126
    :cond_35
    :goto_25
    aget v4, v33, v21

    const/16 v31, 0x0

    aget v5, v33, v31

    aget v7, v33, v16

    .line 127
    invoke-static {v2, v7}, Ljava/lang/Math;->max(II)I

    move-result v2

    .line 128
    invoke-static {v5, v2}, Ljava/lang/Math;->max(II)I

    move-result v2

    .line 129
    invoke-static {v4, v2}, Ljava/lang/Math;->max(II)I

    move-result v2

    .line 130
    aget v4, v28, v21

    aget v5, v28, v31

    aget v7, v28, v17

    aget v12, v28, v16

    .line 131
    invoke-static {v7, v12}, Ljava/lang/Math;->max(II)I

    move-result v7

    .line 132
    invoke-static {v5, v7}, Ljava/lang/Math;->max(II)I

    move-result v5

    .line 133
    invoke-static {v4, v5}, Ljava/lang/Math;->max(II)I

    move-result v4

    add-int/2addr v2, v4

    .line 134
    invoke-static {v6, v2}, Ljava/lang/Math;->max(II)I

    move-result v2

    :goto_26
    move/from16 v24, v9

    move v5, v11

    :goto_27
    if-nez v25, :cond_36

    const/high16 v7, 0x40000000    # 2.0f

    if-eq v10, v7, :cond_36

    move v2, v5

    .line 135
    :cond_36
    invoke-virtual {v0}, Landroid/view/View;->getPaddingTop()I

    move-result v4

    invoke-virtual {v0}, Landroid/view/View;->getPaddingBottom()I

    move-result v5

    add-int/2addr v4, v5

    add-int/2addr v2, v4

    .line 136
    invoke-virtual {v0}, Landroid/view/View;->getSuggestedMinimumHeight()I

    move-result v4

    invoke-static {v2, v4}, Ljava/lang/Math;->max(II)I

    move-result v2

    and-int v4, v24, v22

    or-int v4, v27, v4

    shl-int/lit8 v5, v24, 0x10

    .line 137
    invoke-static {v2, v1, v5}, Landroid/view/View;->resolveSizeAndState(III)I

    move-result v1

    .line 138
    invoke-virtual {v0, v4, v1}, Landroid/view/View;->setMeasuredDimension(II)V

    if-eqz v26, :cond_37

    .line 139
    invoke-direct {v0, v8, v3}, Landroidx/appcompat/widget/y;->f(II)V

    :cond_37
    return-void
.end method

.method public setBaselineAligned(Z)V
    .locals 0

    .line 1
    iput-boolean p1, p0, Landroidx/appcompat/widget/y;->a:Z

    .line 2
    .line 3
    return-void
.end method

.method public setBaselineAlignedChildIndex(I)V
    .locals 2

    .line 1
    if-ltz p1, :cond_0

    .line 2
    .line 3
    invoke-virtual {p0}, Landroid/view/ViewGroup;->getChildCount()I

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    if-ge p1, v0, :cond_0

    .line 8
    .line 9
    iput p1, p0, Landroidx/appcompat/widget/y;->b:I

    .line 10
    .line 11
    return-void

    .line 12
    :cond_0
    new-instance p1, Ljava/lang/IllegalArgumentException;

    .line 13
    .line 14
    new-instance v0, Ljava/lang/StringBuilder;

    .line 15
    .line 16
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    .line 17
    .line 18
    .line 19
    const-string v1, "base aligned child index out of range (0, "

    .line 20
    .line 21
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 22
    .line 23
    .line 24
    invoke-virtual {p0}, Landroid/view/ViewGroup;->getChildCount()I

    .line 25
    .line 26
    .line 27
    move-result v1

    .line 28
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    .line 29
    .line 30
    .line 31
    const-string v1, ")"

    .line 32
    .line 33
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 34
    .line 35
    .line 36
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 37
    .line 38
    .line 39
    move-result-object v0

    .line 40
    invoke-direct {p1, v0}, Ljava/lang/IllegalArgumentException;-><init>(Ljava/lang/String;)V

    .line 41
    .line 42
    .line 43
    throw p1
.end method

.method public setDividerDrawable(Landroid/graphics/drawable/Drawable;)V
    .locals 2

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/y;->k:Landroid/graphics/drawable/Drawable;

    .line 2
    .line 3
    if-ne p1, v0, :cond_0

    .line 4
    .line 5
    return-void

    .line 6
    :cond_0
    iput-object p1, p0, Landroidx/appcompat/widget/y;->k:Landroid/graphics/drawable/Drawable;

    .line 7
    .line 8
    const/4 v0, 0x0

    .line 9
    if-eqz p1, :cond_1

    .line 10
    .line 11
    invoke-virtual {p1}, Landroid/graphics/drawable/Drawable;->getIntrinsicWidth()I

    .line 12
    .line 13
    .line 14
    move-result v1

    .line 15
    iput v1, p0, Landroidx/appcompat/widget/y;->l:I

    .line 16
    .line 17
    invoke-virtual {p1}, Landroid/graphics/drawable/Drawable;->getIntrinsicHeight()I

    .line 18
    .line 19
    .line 20
    move-result v1

    .line 21
    iput v1, p0, Landroidx/appcompat/widget/y;->m:I

    .line 22
    .line 23
    goto :goto_0

    .line 24
    :cond_1
    iput v0, p0, Landroidx/appcompat/widget/y;->l:I

    .line 25
    .line 26
    iput v0, p0, Landroidx/appcompat/widget/y;->m:I

    .line 27
    .line 28
    :goto_0
    if-nez p1, :cond_2

    .line 29
    .line 30
    const/4 v0, 0x1

    .line 31
    :cond_2
    invoke-virtual {p0, v0}, Landroid/view/View;->setWillNotDraw(Z)V

    .line 32
    .line 33
    .line 34
    invoke-virtual {p0}, Landroid/view/View;->requestLayout()V

    .line 35
    .line 36
    .line 37
    return-void
.end method

.method public setDividerPadding(I)V
    .locals 0

    .line 1
    iput p1, p0, Landroidx/appcompat/widget/y;->o:I

    .line 2
    .line 3
    return-void
.end method

.method public setGravity(I)V
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->e:I

    .line 2
    .line 3
    if-eq v0, p1, :cond_2

    .line 4
    .line 5
    const v0, 0x800007

    .line 6
    .line 7
    .line 8
    and-int/2addr v0, p1

    .line 9
    if-nez v0, :cond_0

    .line 10
    .line 11
    const v0, 0x800003

    .line 12
    .line 13
    .line 14
    or-int/2addr p1, v0

    .line 15
    :cond_0
    and-int/lit8 v0, p1, 0x70

    .line 16
    .line 17
    if-nez v0, :cond_1

    .line 18
    .line 19
    or-int/lit8 p1, p1, 0x30

    .line 20
    .line 21
    :cond_1
    iput p1, p0, Landroidx/appcompat/widget/y;->e:I

    .line 22
    .line 23
    invoke-virtual {p0}, Landroid/view/View;->requestLayout()V

    .line 24
    .line 25
    .line 26
    :cond_2
    return-void
.end method

.method public setHorizontalGravity(I)V
    .locals 2

    .line 1
    const v0, 0x800007

    .line 2
    .line 3
    .line 4
    and-int/2addr p1, v0

    .line 5
    iget v1, p0, Landroidx/appcompat/widget/y;->e:I

    .line 6
    .line 7
    and-int/2addr v0, v1

    .line 8
    if-eq v0, p1, :cond_0

    .line 9
    .line 10
    const v0, -0x800008

    .line 11
    .line 12
    .line 13
    and-int/2addr v0, v1

    .line 14
    or-int/2addr p1, v0

    .line 15
    iput p1, p0, Landroidx/appcompat/widget/y;->e:I

    .line 16
    .line 17
    invoke-virtual {p0}, Landroid/view/View;->requestLayout()V

    .line 18
    .line 19
    .line 20
    :cond_0
    return-void
.end method

.method public setMeasureWithLargestChildEnabled(Z)V
    .locals 0

    .line 1
    iput-boolean p1, p0, Landroidx/appcompat/widget/y;->h:Z

    .line 2
    .line 3
    return-void
.end method

.method public setOrientation(I)V
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->d:I

    .line 2
    .line 3
    if-eq v0, p1, :cond_0

    .line 4
    .line 5
    iput p1, p0, Landroidx/appcompat/widget/y;->d:I

    .line 6
    .line 7
    invoke-virtual {p0}, Landroid/view/View;->requestLayout()V

    .line 8
    .line 9
    .line 10
    :cond_0
    return-void
.end method

.method public setShowDividers(I)V
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/y;->n:I

    .line 2
    .line 3
    if-eq p1, v0, :cond_0

    .line 4
    .line 5
    invoke-virtual {p0}, Landroid/view/View;->requestLayout()V

    .line 6
    .line 7
    .line 8
    :cond_0
    iput p1, p0, Landroidx/appcompat/widget/y;->n:I

    .line 9
    .line 10
    return-void
.end method

.method public setVerticalGravity(I)V
    .locals 2

    .line 1
    and-int/lit8 p1, p1, 0x70

    .line 2
    .line 3
    iget v0, p0, Landroidx/appcompat/widget/y;->e:I

    .line 4
    .line 5
    and-int/lit8 v1, v0, 0x70

    .line 6
    .line 7
    if-eq v1, p1, :cond_0

    .line 8
    .line 9
    and-int/lit8 v0, v0, -0x71

    .line 10
    .line 11
    or-int/2addr p1, v0

    .line 12
    iput p1, p0, Landroidx/appcompat/widget/y;->e:I

    .line 13
    .line 14
    invoke-virtual {p0}, Landroid/view/View;->requestLayout()V

    .line 15
    .line 16
    .line 17
    :cond_0
    return-void
.end method

.method public setWeightSum(F)V
    .locals 1

    .line 1
    const/4 v0, 0x0

    .line 2
    invoke-static {v0, p1}, Ljava/lang/Math;->max(FF)F

    .line 3
    .line 4
    .line 5
    move-result p1

    .line 6
    iput p1, p0, Landroidx/appcompat/widget/y;->g:F

    .line 7
    .line 8
    return-void
.end method

.method public shouldDelayChildPressedState()Z
    .locals 1

    const/4 v0, 0x0

    return v0
.end method

.method t(I)I
    .locals 0

    .line 1
    const/4 p1, 0x0

    return p1
.end method

.method u(II)V
    .locals 27

    move-object/from16 v0, p0

    const/4 v7, 0x0

    .line 1
    iput v7, v0, Landroidx/appcompat/widget/y;->f:I

    .line 2
    invoke-virtual {v0}, Landroidx/appcompat/widget/y;->getVirtualChildCount()I

    move-result v8

    .line 3
    invoke-static/range {p1 .. p1}, Landroid/view/View$MeasureSpec;->getMode(I)I

    move-result v9

    .line 4
    invoke-static/range {p2 .. p2}, Landroid/view/View$MeasureSpec;->getMode(I)I

    move-result v10

    .line 5
    iget v11, v0, Landroidx/appcompat/widget/y;->b:I

    .line 6
    iget-boolean v12, v0, Landroidx/appcompat/widget/y;->h:Z

    move v2, v7

    move v3, v2

    move v4, v3

    move v5, v4

    move v6, v5

    move v15, v6

    move/from16 v16, v15

    move/from16 v18, v16

    const/4 v1, 0x0

    const/16 v17, 0x1

    const/16 v19, 0x1

    :goto_0
    const/16 v20, 0x0

    const/16 v7, 0x8

    const/high16 v14, 0x40000000    # 2.0f

    if-ge v2, v8, :cond_11

    move/from16 v21, v1

    .line 7
    invoke-virtual {v0, v2}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    move-result-object v1

    if-nez v1, :cond_0

    .line 8
    iget v1, v0, Landroidx/appcompat/widget/y;->f:I

    invoke-virtual {v0, v2}, Landroidx/appcompat/widget/y;->t(I)I

    move-result v7

    add-int/2addr v1, v7

    iput v1, v0, Landroidx/appcompat/widget/y;->f:I

    :goto_1
    move v14, v3

    move/from16 v26, v8

    move/from16 v25, v10

    move/from16 v24, v12

    move/from16 v1, v21

    move/from16 v3, p1

    move v10, v5

    move/from16 v5, p2

    goto/16 :goto_c

    .line 9
    :cond_0
    invoke-virtual {v1}, Landroid/view/View;->getVisibility()I

    move-result v13

    if-ne v13, v7, :cond_1

    .line 10
    invoke-virtual {v0, v1, v2}, Landroidx/appcompat/widget/y;->k(Landroid/view/View;I)I

    move-result v1

    add-int/2addr v2, v1

    goto :goto_1

    .line 11
    :cond_1
    invoke-virtual {v0, v2}, Landroidx/appcompat/widget/y;->o(I)Z

    move-result v7

    if-eqz v7, :cond_2

    .line 12
    iget v7, v0, Landroidx/appcompat/widget/y;->f:I

    iget v13, v0, Landroidx/appcompat/widget/y;->m:I

    add-int/2addr v7, v13

    iput v7, v0, Landroidx/appcompat/widget/y;->f:I

    .line 13
    :cond_2
    invoke-virtual {v1}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v7

    check-cast v7, Landroidx/appcompat/widget/y$a;

    .line 14
    iget v13, v7, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    add-float v21, v21, v13

    if-ne v10, v14, :cond_3

    .line 15
    iget v14, v7, Landroid/widget/LinearLayout$LayoutParams;->height:I

    if-nez v14, :cond_3

    cmpl-float v14, v13, v20

    if-lez v14, :cond_3

    .line 16
    iget v13, v0, Landroidx/appcompat/widget/y;->f:I

    .line 17
    iget v14, v7, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    add-int/2addr v14, v13

    move-object/from16 v24, v1

    iget v1, v7, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    add-int/2addr v14, v1

    invoke-static {v13, v14}, Ljava/lang/Math;->max(II)I

    move-result v1

    iput v1, v0, Landroidx/appcompat/widget/y;->f:I

    move v14, v3

    move v1, v4

    move/from16 v26, v8

    move/from16 v25, v10

    move/from16 v16, v19

    move-object/from16 v4, v24

    move/from16 v3, p1

    move v10, v5

    move v8, v6

    move/from16 v24, v12

    move/from16 v5, p2

    goto/16 :goto_5

    :cond_3
    move-object/from16 v24, v1

    .line 18
    iget v1, v7, Landroid/widget/LinearLayout$LayoutParams;->height:I

    if-nez v1, :cond_4

    cmpl-float v1, v13, v20

    if-lez v1, :cond_4

    const/4 v1, -0x2

    .line 19
    iput v1, v7, Landroid/widget/LinearLayout$LayoutParams;->height:I

    const/4 v13, 0x0

    goto :goto_2

    :cond_4
    const/high16 v13, -0x80000000

    :goto_2
    cmpl-float v1, v21, v20

    if-nez v1, :cond_5

    .line 20
    iget v1, v0, Landroidx/appcompat/widget/y;->f:I

    move v14, v6

    move v6, v1

    move v1, v14

    :goto_3
    move v14, v4

    goto :goto_4

    :cond_5
    move v1, v6

    const/4 v6, 0x0

    goto :goto_3

    :goto_4
    const/4 v4, 0x0

    move/from16 v26, v8

    move/from16 v25, v10

    move v8, v1

    move v10, v5

    move-object/from16 v1, v24

    move/from16 v5, p2

    move/from16 v24, v12

    move v12, v14

    move v14, v3

    move/from16 v3, p1

    .line 21
    invoke-virtual/range {v0 .. v6}, Landroidx/appcompat/widget/y;->r(Landroid/view/View;IIIII)V

    move-object v4, v1

    const/high16 v1, -0x80000000

    if-eq v13, v1, :cond_6

    .line 22
    iput v13, v7, Landroid/widget/LinearLayout$LayoutParams;->height:I

    .line 23
    :cond_6
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredHeight()I

    move-result v1

    .line 24
    iget v6, v0, Landroidx/appcompat/widget/y;->f:I

    add-int v13, v6, v1

    move/from16 v22, v13

    .line 25
    iget v13, v7, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    add-int v13, v22, v13

    move/from16 v22, v13

    iget v13, v7, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    add-int v13, v22, v13

    .line 26
    invoke-virtual {v0, v4}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    move-result v22

    add-int v13, v13, v22

    .line 27
    invoke-static {v6, v13}, Ljava/lang/Math;->max(II)I

    move-result v6

    iput v6, v0, Landroidx/appcompat/widget/y;->f:I

    if-eqz v24, :cond_7

    .line 28
    invoke-static {v1, v12}, Ljava/lang/Math;->max(II)I

    move-result v1

    goto :goto_5

    :cond_7
    move v1, v12

    :goto_5
    if-ltz v11, :cond_8

    add-int/lit8 v6, v2, 0x1

    if-ne v11, v6, :cond_8

    .line 29
    iget v6, v0, Landroidx/appcompat/widget/y;->f:I

    iput v6, v0, Landroidx/appcompat/widget/y;->c:I

    :cond_8
    if-ge v2, v11, :cond_9

    .line 30
    iget v6, v7, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    cmpl-float v6, v6, v20

    if-gtz v6, :cond_a

    :cond_9
    const/high16 v6, 0x40000000    # 2.0f

    goto :goto_6

    .line 31
    :cond_a
    new-instance v1, Ljava/lang/RuntimeException;

    const-string v2, "A child of LinearLayout with index less than mBaselineAlignedChildIndex has weight > 0, which won\'t work.  Either remove the weight, or don\'t set mBaselineAlignedChildIndex."

    invoke-direct {v1, v2}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/String;)V

    throw v1

    :goto_6
    if-eq v9, v6, :cond_b

    .line 32
    iget v6, v7, Landroid/widget/LinearLayout$LayoutParams;->width:I

    const/4 v12, -0x1

    if-ne v6, v12, :cond_b

    move/from16 v6, v19

    move/from16 v18, v6

    goto :goto_7

    :cond_b
    const/4 v6, 0x0

    .line 33
    :goto_7
    iget v12, v7, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    iget v13, v7, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v12, v13

    .line 34
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredWidth()I

    move-result v13

    add-int/2addr v13, v12

    .line 35
    invoke-static {v10, v13}, Ljava/lang/Math;->max(II)I

    move-result v10

    move/from16 v22, v1

    .line 36
    invoke-virtual {v4}, Landroid/view/View;->getMeasuredState()I

    move-result v1

    .line 37
    invoke-static {v8, v1}, Landroid/view/View;->combineMeasuredStates(II)I

    move-result v1

    if-eqz v17, :cond_c

    .line 38
    iget v8, v7, Landroid/widget/LinearLayout$LayoutParams;->width:I

    move/from16 v23, v1

    const/4 v1, -0x1

    if-ne v8, v1, :cond_d

    move/from16 v17, v19

    goto :goto_8

    :cond_c
    move/from16 v23, v1

    :cond_d
    const/16 v17, 0x0

    .line 39
    :goto_8
    iget v1, v7, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    cmpl-float v1, v1, v20

    if-lez v1, :cond_f

    if-eqz v6, :cond_e

    goto :goto_9

    :cond_e
    move v12, v13

    .line 40
    :goto_9
    invoke-static {v14, v12}, Ljava/lang/Math;->max(II)I

    move-result v1

    move v14, v1

    goto :goto_b

    :cond_f
    if-eqz v6, :cond_10

    goto :goto_a

    :cond_10
    move v12, v13

    .line 41
    :goto_a
    invoke-static {v15, v12}, Ljava/lang/Math;->max(II)I

    move-result v15

    .line 42
    :goto_b
    invoke-virtual {v0, v4, v2}, Landroidx/appcompat/widget/y;->k(Landroid/view/View;I)I

    move-result v1

    add-int/2addr v2, v1

    move/from16 v1, v21

    move/from16 v4, v22

    move/from16 v6, v23

    :goto_c
    add-int/lit8 v2, v2, 0x1

    move v5, v10

    move v3, v14

    move/from16 v12, v24

    move/from16 v10, v25

    move/from16 v8, v26

    const/4 v7, 0x0

    goto/16 :goto_0

    :cond_11
    move/from16 v21, v1

    move v14, v3

    move/from16 v26, v8

    move/from16 v25, v10

    move/from16 v24, v12

    move/from16 v3, p1

    move v12, v4

    move v10, v5

    move v8, v6

    move/from16 v5, p2

    .line 43
    iget v1, v0, Landroidx/appcompat/widget/y;->f:I

    if-lez v1, :cond_12

    move/from16 v1, v26

    invoke-virtual {v0, v1}, Landroidx/appcompat/widget/y;->o(I)Z

    move-result v2

    if-eqz v2, :cond_13

    .line 44
    iget v2, v0, Landroidx/appcompat/widget/y;->f:I

    iget v4, v0, Landroidx/appcompat/widget/y;->m:I

    add-int/2addr v2, v4

    iput v2, v0, Landroidx/appcompat/widget/y;->f:I

    goto :goto_d

    :cond_12
    move/from16 v1, v26

    :cond_13
    :goto_d
    move/from16 v2, v25

    if-eqz v24, :cond_17

    const/high16 v4, -0x80000000

    if-eq v2, v4, :cond_14

    if-nez v2, :cond_17

    :cond_14
    const/4 v4, 0x0

    .line 45
    iput v4, v0, Landroidx/appcompat/widget/y;->f:I

    const/4 v4, 0x0

    :goto_e
    if-ge v4, v1, :cond_17

    .line 46
    invoke-virtual {v0, v4}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    move-result-object v6

    if-nez v6, :cond_15

    .line 47
    iget v6, v0, Landroidx/appcompat/widget/y;->f:I

    invoke-virtual {v0, v4}, Landroidx/appcompat/widget/y;->t(I)I

    move-result v11

    add-int/2addr v6, v11

    iput v6, v0, Landroidx/appcompat/widget/y;->f:I

    goto :goto_f

    .line 48
    :cond_15
    invoke-virtual {v6}, Landroid/view/View;->getVisibility()I

    move-result v11

    if-ne v11, v7, :cond_16

    .line 49
    invoke-virtual {v0, v6, v4}, Landroidx/appcompat/widget/y;->k(Landroid/view/View;I)I

    move-result v6

    add-int/2addr v4, v6

    goto :goto_f

    .line 50
    :cond_16
    invoke-virtual {v6}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v11

    check-cast v11, Landroidx/appcompat/widget/y$a;

    .line 51
    iget v13, v0, Landroidx/appcompat/widget/y;->f:I

    add-int v22, v13, v12

    .line 52
    iget v7, v11, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    add-int v22, v22, v7

    iget v7, v11, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    add-int v22, v22, v7

    .line 53
    invoke-virtual {v0, v6}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    move-result v6

    add-int v6, v22, v6

    .line 54
    invoke-static {v13, v6}, Ljava/lang/Math;->max(II)I

    move-result v6

    iput v6, v0, Landroidx/appcompat/widget/y;->f:I

    :goto_f
    add-int/lit8 v4, v4, 0x1

    const/16 v7, 0x8

    goto :goto_e

    .line 55
    :cond_17
    iget v4, v0, Landroidx/appcompat/widget/y;->f:I

    invoke-virtual {v0}, Landroid/view/View;->getPaddingTop()I

    move-result v6

    invoke-virtual {v0}, Landroid/view/View;->getPaddingBottom()I

    move-result v7

    add-int/2addr v6, v7

    add-int/2addr v4, v6

    iput v4, v0, Landroidx/appcompat/widget/y;->f:I

    .line 56
    invoke-virtual {v0}, Landroid/view/View;->getSuggestedMinimumHeight()I

    move-result v6

    invoke-static {v4, v6}, Ljava/lang/Math;->max(II)I

    move-result v4

    const/4 v6, 0x0

    .line 57
    invoke-static {v4, v5, v6}, Landroid/view/View;->resolveSizeAndState(III)I

    move-result v4

    const v6, 0xffffff

    and-int/2addr v6, v4

    .line 58
    iget v7, v0, Landroidx/appcompat/widget/y;->f:I

    sub-int/2addr v6, v7

    if-nez v16, :cond_1b

    if-eqz v6, :cond_18

    cmpl-float v7, v21, v20

    if-lez v7, :cond_18

    goto :goto_12

    .line 59
    :cond_18
    invoke-static {v15, v14}, Ljava/lang/Math;->max(II)I

    move-result v6

    if-eqz v24, :cond_27

    const/high16 v7, 0x40000000    # 2.0f

    if-eq v2, v7, :cond_27

    const/4 v7, 0x0

    :goto_10
    if-ge v7, v1, :cond_27

    .line 60
    invoke-virtual {v0, v7}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    move-result-object v2

    if-eqz v2, :cond_1a

    .line 61
    invoke-virtual {v2}, Landroid/view/View;->getVisibility()I

    move-result v11

    const/16 v13, 0x8

    if-ne v11, v13, :cond_19

    goto :goto_11

    .line 62
    :cond_19
    invoke-virtual {v2}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v11

    check-cast v11, Landroidx/appcompat/widget/y$a;

    .line 63
    iget v11, v11, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    cmpl-float v11, v11, v20

    if-lez v11, :cond_1a

    .line 64
    invoke-virtual {v2}, Landroid/view/View;->getMeasuredWidth()I

    move-result v11

    const/high16 v13, 0x40000000    # 2.0f

    invoke-static {v11, v13}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v11

    .line 65
    invoke-static {v12, v13}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v14

    .line 66
    invoke-virtual {v2, v11, v14}, Landroid/view/View;->measure(II)V

    :cond_1a
    :goto_11
    add-int/lit8 v7, v7, 0x1

    goto :goto_10

    .line 67
    :cond_1b
    :goto_12
    iget v7, v0, Landroidx/appcompat/widget/y;->g:F

    cmpl-float v11, v7, v20

    if-lez v11, :cond_1c

    :goto_13
    const/4 v11, 0x0

    goto :goto_14

    :cond_1c
    move/from16 v7, v21

    goto :goto_13

    .line 68
    :goto_14
    iput v11, v0, Landroidx/appcompat/widget/y;->f:I

    move v12, v7

    move v7, v6

    move v6, v11

    :goto_15
    if-ge v6, v1, :cond_26

    .line 69
    invoke-virtual {v0, v6}, Landroidx/appcompat/widget/y;->n(I)Landroid/view/View;

    move-result-object v13

    .line 70
    invoke-virtual {v13}, Landroid/view/View;->getVisibility()I

    move-result v14

    const/16 v11, 0x8

    if-ne v14, v11, :cond_1d

    move/from16 v22, v2

    move/from16 v16, v6

    goto/16 :goto_1d

    .line 71
    :cond_1d
    invoke-virtual {v13}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v14

    check-cast v14, Landroidx/appcompat/widget/y$a;

    .line 72
    iget v11, v14, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    cmpl-float v16, v11, v20

    if-lez v16, :cond_22

    move/from16 v16, v6

    int-to-float v6, v7

    mul-float/2addr v6, v11

    div-float/2addr v6, v12

    float-to-int v6, v6

    sub-float/2addr v12, v11

    sub-int/2addr v7, v6

    .line 73
    invoke-virtual {v0}, Landroid/view/View;->getPaddingLeft()I

    move-result v11

    invoke-virtual {v0}, Landroid/view/View;->getPaddingRight()I

    move-result v21

    add-int v11, v11, v21

    move/from16 v21, v6

    iget v6, v14, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    add-int/2addr v11, v6

    iget v6, v14, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v11, v6

    iget v6, v14, Landroid/widget/LinearLayout$LayoutParams;->width:I

    .line 74
    invoke-static {v3, v11, v6}, Landroid/view/ViewGroup;->getChildMeasureSpec(III)I

    move-result v6

    .line 75
    iget v11, v14, Landroid/widget/LinearLayout$LayoutParams;->height:I

    if-nez v11, :cond_20

    const/high16 v11, 0x40000000    # 2.0f

    if-eq v2, v11, :cond_1e

    :goto_16
    move/from16 v22, v2

    goto :goto_18

    :cond_1e
    move/from16 v22, v2

    if-lez v21, :cond_1f

    move/from16 v2, v21

    goto :goto_17

    :cond_1f
    const/4 v2, 0x0

    .line 76
    :goto_17
    invoke-static {v2, v11}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v2

    .line 77
    invoke-virtual {v13, v6, v2}, Landroid/view/View;->measure(II)V

    goto :goto_19

    :cond_20
    const/high16 v11, 0x40000000    # 2.0f

    goto :goto_16

    .line 78
    :goto_18
    invoke-virtual {v13}, Landroid/view/View;->getMeasuredHeight()I

    move-result v2

    add-int v2, v2, v21

    if-gez v2, :cond_21

    const/4 v2, 0x0

    .line 79
    :cond_21
    invoke-static {v2, v11}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    move-result v2

    .line 80
    invoke-virtual {v13, v6, v2}, Landroid/view/View;->measure(II)V

    .line 81
    :goto_19
    invoke-virtual {v13}, Landroid/view/View;->getMeasuredState()I

    move-result v2

    and-int/lit16 v2, v2, -0x100

    .line 82
    invoke-static {v8, v2}, Landroid/view/View;->combineMeasuredStates(II)I

    move-result v8

    goto :goto_1a

    :cond_22
    move/from16 v22, v2

    move/from16 v16, v6

    .line 83
    :goto_1a
    iget v2, v14, Landroid/widget/LinearLayout$LayoutParams;->leftMargin:I

    iget v6, v14, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    add-int/2addr v2, v6

    .line 84
    invoke-virtual {v13}, Landroid/view/View;->getMeasuredWidth()I

    move-result v6

    add-int/2addr v6, v2

    .line 85
    invoke-static {v10, v6}, Ljava/lang/Math;->max(II)I

    move-result v10

    const/high16 v11, 0x40000000    # 2.0f

    if-eq v9, v11, :cond_23

    .line 86
    iget v11, v14, Landroid/widget/LinearLayout$LayoutParams;->width:I

    move/from16 v21, v2

    const/4 v2, -0x1

    if-ne v11, v2, :cond_24

    move/from16 v6, v21

    goto :goto_1b

    :cond_23
    const/4 v2, -0x1

    .line 87
    :cond_24
    :goto_1b
    invoke-static {v15, v6}, Ljava/lang/Math;->max(II)I

    move-result v6

    if-eqz v17, :cond_25

    .line 88
    iget v11, v14, Landroid/widget/LinearLayout$LayoutParams;->width:I

    if-ne v11, v2, :cond_25

    move/from16 v11, v19

    goto :goto_1c

    :cond_25
    const/4 v11, 0x0

    .line 89
    :goto_1c
    iget v15, v0, Landroidx/appcompat/widget/y;->f:I

    .line 90
    invoke-virtual {v13}, Landroid/view/View;->getMeasuredHeight()I

    move-result v17

    add-int v17, v15, v17

    iget v2, v14, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    add-int v17, v17, v2

    iget v2, v14, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    add-int v17, v17, v2

    .line 91
    invoke-virtual {v0, v13}, Landroidx/appcompat/widget/y;->m(Landroid/view/View;)I

    move-result v2

    add-int v2, v17, v2

    .line 92
    invoke-static {v15, v2}, Ljava/lang/Math;->max(II)I

    move-result v2

    iput v2, v0, Landroidx/appcompat/widget/y;->f:I

    move v15, v6

    move/from16 v17, v11

    :goto_1d
    add-int/lit8 v6, v16, 0x1

    move/from16 v2, v22

    const/4 v11, 0x0

    goto/16 :goto_15

    .line 93
    :cond_26
    iget v2, v0, Landroidx/appcompat/widget/y;->f:I

    invoke-virtual {v0}, Landroid/view/View;->getPaddingTop()I

    move-result v6

    invoke-virtual {v0}, Landroid/view/View;->getPaddingBottom()I

    move-result v7

    add-int/2addr v6, v7

    add-int/2addr v2, v6

    iput v2, v0, Landroidx/appcompat/widget/y;->f:I

    move v6, v15

    :cond_27
    if-nez v17, :cond_28

    const/high16 v11, 0x40000000    # 2.0f

    if-eq v9, v11, :cond_28

    move v10, v6

    .line 94
    :cond_28
    invoke-virtual {v0}, Landroid/view/View;->getPaddingLeft()I

    move-result v2

    invoke-virtual {v0}, Landroid/view/View;->getPaddingRight()I

    move-result v6

    add-int/2addr v2, v6

    add-int/2addr v10, v2

    .line 95
    invoke-virtual {v0}, Landroid/view/View;->getSuggestedMinimumWidth()I

    move-result v2

    invoke-static {v10, v2}, Ljava/lang/Math;->max(II)I

    move-result v2

    .line 96
    invoke-static {v2, v3, v8}, Landroid/view/View;->resolveSizeAndState(III)I

    move-result v2

    invoke-virtual {v0, v2, v4}, Landroid/view/View;->setMeasuredDimension(II)V

    if-eqz v18, :cond_29

    .line 97
    invoke-direct {v0, v1, v5}, Landroidx/appcompat/widget/y;->g(II)V

    :cond_29
    return-void
.end method
