.class public abstract Landroidx/appcompat/widget/z;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Lj/b;


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Landroidx/appcompat/widget/z$i;,
        Landroidx/appcompat/widget/z$h;,
        Landroidx/appcompat/widget/z$g;,
        Landroidx/appcompat/widget/z$e;,
        Landroidx/appcompat/widget/z$f;,
        Landroidx/appcompat/widget/z$d;,
        Landroidx/appcompat/widget/z$c;
    }
.end annotation


# static fields
.field private static G:Ljava/lang/reflect/Method;

.field private static H:Ljava/lang/reflect/Method;


# instance fields
.field private A:Ljava/lang/Runnable;

.field final B:Landroid/os/Handler;

.field private final C:Landroid/graphics/Rect;

.field private D:Landroid/graphics/Rect;

.field private E:Z

.field F:Landroid/widget/PopupWindow;

.field private a:Landroid/content/Context;

.field private b:Landroid/widget/ListAdapter;

.field c:Landroidx/appcompat/widget/v;

.field private d:I

.field private e:I

.field private f:I

.field private g:I

.field private h:I

.field private i:Z

.field private j:Z

.field private k:Z

.field private l:I

.field private m:Z

.field private n:Z

.field o:I

.field private p:Landroid/view/View;

.field private q:I

.field private r:Landroid/database/DataSetObserver;

.field private s:Landroid/view/View;

.field private t:Landroid/graphics/drawable/Drawable;

.field private u:Landroid/widget/AdapterView$OnItemClickListener;

.field private v:Landroid/widget/AdapterView$OnItemSelectedListener;

.field final w:Landroidx/appcompat/widget/z$i;

.field private final x:Landroidx/appcompat/widget/z$h;

.field private final y:Landroidx/appcompat/widget/z$g;

.field private final z:Landroidx/appcompat/widget/z$e;


# direct methods
.method static constructor <clinit>()V
    .locals 4

    .line 1
    const-string v0, "ListPopupWindow"

    .line 2
    .line 3
    const-class v1, Landroid/widget/PopupWindow;

    .line 4
    .line 5
    sget v2, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 6
    .line 7
    const/16 v3, 0x1c

    .line 8
    .line 9
    if-gt v2, v3, :cond_0

    .line 10
    .line 11
    :try_start_0
    const-string v2, "setClipToScreenEnabled"

    .line 12
    .line 13
    sget-object v3, Ljava/lang/Boolean;->TYPE:Ljava/lang/Class;

    .line 14
    .line 15
    filled-new-array {v3}, [Ljava/lang/Class;

    .line 16
    .line 17
    .line 18
    move-result-object v3

    .line 19
    invoke-virtual {v1, v2, v3}, Ljava/lang/Class;->getDeclaredMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    .line 20
    .line 21
    .line 22
    move-result-object v2

    .line 23
    sput-object v2, Landroidx/appcompat/widget/z;->G:Ljava/lang/reflect/Method;
    :try_end_0
    .catch Ljava/lang/NoSuchMethodException; {:try_start_0 .. :try_end_0} :catch_0

    .line 24
    .line 25
    goto :goto_0

    .line 26
    :catch_0
    const-string v2, "Could not find method setClipToScreenEnabled() on PopupWindow. Oh well."

    .line 27
    .line 28
    invoke-static {v0, v2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 29
    .line 30
    .line 31
    :goto_0
    :try_start_1
    const-string v2, "setEpicenterBounds"

    .line 32
    .line 33
    const-class v3, Landroid/graphics/Rect;

    .line 34
    .line 35
    filled-new-array {v3}, [Ljava/lang/Class;

    .line 36
    .line 37
    .line 38
    move-result-object v3

    .line 39
    invoke-virtual {v1, v2, v3}, Ljava/lang/Class;->getDeclaredMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    .line 40
    .line 41
    .line 42
    move-result-object v1

    .line 43
    sput-object v1, Landroidx/appcompat/widget/z;->H:Ljava/lang/reflect/Method;
    :try_end_1
    .catch Ljava/lang/NoSuchMethodException; {:try_start_1 .. :try_end_1} :catch_1

    .line 44
    .line 45
    goto :goto_1

    .line 46
    :catch_1
    const-string v1, "Could not find method setEpicenterBounds(Rect) on PopupWindow. Oh well."

    .line 47
    .line 48
    invoke-static {v0, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 49
    .line 50
    .line 51
    :cond_0
    :goto_1
    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;II)V
    .locals 3

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 2
    .line 3
    .line 4
    const/4 v0, -0x2

    .line 5
    iput v0, p0, Landroidx/appcompat/widget/z;->d:I

    .line 6
    .line 7
    iput v0, p0, Landroidx/appcompat/widget/z;->e:I

    .line 8
    .line 9
    const/16 v0, 0x3ea

    .line 10
    .line 11
    iput v0, p0, Landroidx/appcompat/widget/z;->h:I

    .line 12
    .line 13
    const/4 v0, 0x0

    .line 14
    iput v0, p0, Landroidx/appcompat/widget/z;->l:I

    .line 15
    .line 16
    iput-boolean v0, p0, Landroidx/appcompat/widget/z;->m:Z

    .line 17
    .line 18
    iput-boolean v0, p0, Landroidx/appcompat/widget/z;->n:Z

    .line 19
    .line 20
    const v1, 0x7fffffff

    .line 21
    .line 22
    .line 23
    iput v1, p0, Landroidx/appcompat/widget/z;->o:I

    .line 24
    .line 25
    iput v0, p0, Landroidx/appcompat/widget/z;->q:I

    .line 26
    .line 27
    new-instance v1, Landroidx/appcompat/widget/z$i;

    .line 28
    .line 29
    invoke-direct {v1, p0}, Landroidx/appcompat/widget/z$i;-><init>(Landroidx/appcompat/widget/z;)V

    .line 30
    .line 31
    .line 32
    iput-object v1, p0, Landroidx/appcompat/widget/z;->w:Landroidx/appcompat/widget/z$i;

    .line 33
    .line 34
    new-instance v1, Landroidx/appcompat/widget/z$h;

    .line 35
    .line 36
    invoke-direct {v1, p0}, Landroidx/appcompat/widget/z$h;-><init>(Landroidx/appcompat/widget/z;)V

    .line 37
    .line 38
    .line 39
    iput-object v1, p0, Landroidx/appcompat/widget/z;->x:Landroidx/appcompat/widget/z$h;

    .line 40
    .line 41
    new-instance v1, Landroidx/appcompat/widget/z$g;

    .line 42
    .line 43
    invoke-direct {v1, p0}, Landroidx/appcompat/widget/z$g;-><init>(Landroidx/appcompat/widget/z;)V

    .line 44
    .line 45
    .line 46
    iput-object v1, p0, Landroidx/appcompat/widget/z;->y:Landroidx/appcompat/widget/z$g;

    .line 47
    .line 48
    new-instance v1, Landroidx/appcompat/widget/z$e;

    .line 49
    .line 50
    invoke-direct {v1, p0}, Landroidx/appcompat/widget/z$e;-><init>(Landroidx/appcompat/widget/z;)V

    .line 51
    .line 52
    .line 53
    iput-object v1, p0, Landroidx/appcompat/widget/z;->z:Landroidx/appcompat/widget/z$e;

    .line 54
    .line 55
    new-instance v1, Landroid/graphics/Rect;

    .line 56
    .line 57
    invoke-direct {v1}, Landroid/graphics/Rect;-><init>()V

    .line 58
    .line 59
    .line 60
    iput-object v1, p0, Landroidx/appcompat/widget/z;->C:Landroid/graphics/Rect;

    .line 61
    .line 62
    iput-object p1, p0, Landroidx/appcompat/widget/z;->a:Landroid/content/Context;

    .line 63
    .line 64
    new-instance v1, Landroid/os/Handler;

    .line 65
    .line 66
    invoke-virtual {p1}, Landroid/content/Context;->getMainLooper()Landroid/os/Looper;

    .line 67
    .line 68
    .line 69
    move-result-object v2

    .line 70
    invoke-direct {v1, v2}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    .line 71
    .line 72
    .line 73
    iput-object v1, p0, Landroidx/appcompat/widget/z;->B:Landroid/os/Handler;

    .line 74
    .line 75
    sget-object v1, Ld/i;->C0:[I

    .line 76
    .line 77
    invoke-virtual {p1, p2, v1, p3, p4}, Landroid/content/Context;->obtainStyledAttributes(Landroid/util/AttributeSet;[III)Landroid/content/res/TypedArray;

    .line 78
    .line 79
    .line 80
    move-result-object v1

    .line 81
    sget v2, Ld/i;->D0:I

    .line 82
    .line 83
    invoke-virtual {v1, v2, v0}, Landroid/content/res/TypedArray;->getDimensionPixelOffset(II)I

    .line 84
    .line 85
    .line 86
    move-result v2

    .line 87
    iput v2, p0, Landroidx/appcompat/widget/z;->f:I

    .line 88
    .line 89
    sget v2, Ld/i;->E0:I

    .line 90
    .line 91
    invoke-virtual {v1, v2, v0}, Landroid/content/res/TypedArray;->getDimensionPixelOffset(II)I

    .line 92
    .line 93
    .line 94
    move-result v0

    .line 95
    iput v0, p0, Landroidx/appcompat/widget/z;->g:I

    .line 96
    .line 97
    const/4 v2, 0x1

    .line 98
    if-eqz v0, :cond_0

    .line 99
    .line 100
    iput-boolean v2, p0, Landroidx/appcompat/widget/z;->i:Z

    .line 101
    .line 102
    :cond_0
    invoke-virtual {v1}, Landroid/content/res/TypedArray;->recycle()V

    .line 103
    .line 104
    .line 105
    new-instance v0, Landroidx/appcompat/widget/m;

    .line 106
    .line 107
    invoke-direct {v0, p1, p2, p3, p4}, Landroidx/appcompat/widget/m;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;II)V

    .line 108
    .line 109
    .line 110
    iput-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 111
    .line 112
    invoke-virtual {v0, v2}, Landroid/widget/PopupWindow;->setInputMethodMode(I)V

    .line 113
    .line 114
    .line 115
    return-void
.end method

.method private C(Z)V
    .locals 2

    .line 1
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 2
    .line 3
    const/16 v1, 0x1c

    .line 4
    .line 5
    if-gt v0, v1, :cond_1

    .line 6
    .line 7
    sget-object v0, Landroidx/appcompat/widget/z;->G:Ljava/lang/reflect/Method;

    .line 8
    .line 9
    if-eqz v0, :cond_0

    .line 10
    .line 11
    :try_start_0
    iget-object v1, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 12
    .line 13
    invoke-static {p1}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    .line 14
    .line 15
    .line 16
    move-result-object p1

    .line 17
    filled-new-array {p1}, [Ljava/lang/Object;

    .line 18
    .line 19
    .line 20
    move-result-object p1

    .line 21
    invoke-virtual {v0, v1, p1}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 22
    .line 23
    .line 24
    return-void

    .line 25
    :catch_0
    const-string p1, "ListPopupWindow"

    .line 26
    .line 27
    const-string v0, "Could not call setClipToScreenEnabled() on PopupWindow. Oh well."

    .line 28
    .line 29
    invoke-static {p1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 30
    .line 31
    .line 32
    :cond_0
    return-void

    .line 33
    :cond_1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 34
    .line 35
    invoke-static {v0, p1}, Landroidx/appcompat/widget/z$d;->b(Landroid/widget/PopupWindow;Z)V

    .line 36
    .line 37
    .line 38
    return-void
.end method

.method private f()I
    .locals 12

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 2
    .line 3
    const/high16 v1, -0x80000000

    .line 4
    .line 5
    const/4 v2, -0x1

    .line 6
    const/4 v3, 0x1

    .line 7
    const/4 v4, 0x0

    .line 8
    if-nez v0, :cond_6

    .line 9
    .line 10
    iget-object v0, p0, Landroidx/appcompat/widget/z;->a:Landroid/content/Context;

    .line 11
    .line 12
    new-instance v5, Landroidx/appcompat/widget/z$a;

    .line 13
    .line 14
    invoke-direct {v5, p0}, Landroidx/appcompat/widget/z$a;-><init>(Landroidx/appcompat/widget/z;)V

    .line 15
    .line 16
    .line 17
    iput-object v5, p0, Landroidx/appcompat/widget/z;->A:Ljava/lang/Runnable;

    .line 18
    .line 19
    iget-boolean v5, p0, Landroidx/appcompat/widget/z;->E:Z

    .line 20
    .line 21
    xor-int/2addr v5, v3

    .line 22
    invoke-virtual {p0, v0, v5}, Landroidx/appcompat/widget/z;->h(Landroid/content/Context;Z)Landroidx/appcompat/widget/v;

    .line 23
    .line 24
    .line 25
    move-result-object v5

    .line 26
    iput-object v5, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 27
    .line 28
    iget-object v6, p0, Landroidx/appcompat/widget/z;->t:Landroid/graphics/drawable/Drawable;

    .line 29
    .line 30
    if-eqz v6, :cond_0

    .line 31
    .line 32
    invoke-virtual {v5, v6}, Landroidx/appcompat/widget/v;->setSelector(Landroid/graphics/drawable/Drawable;)V

    .line 33
    .line 34
    .line 35
    :cond_0
    iget-object v5, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 36
    .line 37
    iget-object v6, p0, Landroidx/appcompat/widget/z;->b:Landroid/widget/ListAdapter;

    .line 38
    .line 39
    invoke-virtual {v5, v6}, Landroid/widget/AbsListView;->setAdapter(Landroid/widget/ListAdapter;)V

    .line 40
    .line 41
    .line 42
    iget-object v5, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 43
    .line 44
    iget-object v6, p0, Landroidx/appcompat/widget/z;->u:Landroid/widget/AdapterView$OnItemClickListener;

    .line 45
    .line 46
    invoke-virtual {v5, v6}, Landroid/widget/AdapterView;->setOnItemClickListener(Landroid/widget/AdapterView$OnItemClickListener;)V

    .line 47
    .line 48
    .line 49
    iget-object v5, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 50
    .line 51
    invoke-virtual {v5, v3}, Landroid/view/View;->setFocusable(Z)V

    .line 52
    .line 53
    .line 54
    iget-object v5, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 55
    .line 56
    invoke-virtual {v5, v3}, Landroid/view/View;->setFocusableInTouchMode(Z)V

    .line 57
    .line 58
    .line 59
    iget-object v5, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 60
    .line 61
    new-instance v6, Landroidx/appcompat/widget/z$b;

    .line 62
    .line 63
    invoke-direct {v6, p0}, Landroidx/appcompat/widget/z$b;-><init>(Landroidx/appcompat/widget/z;)V

    .line 64
    .line 65
    .line 66
    invoke-virtual {v5, v6}, Landroid/widget/AdapterView;->setOnItemSelectedListener(Landroid/widget/AdapterView$OnItemSelectedListener;)V

    .line 67
    .line 68
    .line 69
    iget-object v5, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 70
    .line 71
    iget-object v6, p0, Landroidx/appcompat/widget/z;->y:Landroidx/appcompat/widget/z$g;

    .line 72
    .line 73
    invoke-virtual {v5, v6}, Landroid/widget/AbsListView;->setOnScrollListener(Landroid/widget/AbsListView$OnScrollListener;)V

    .line 74
    .line 75
    .line 76
    iget-object v5, p0, Landroidx/appcompat/widget/z;->v:Landroid/widget/AdapterView$OnItemSelectedListener;

    .line 77
    .line 78
    if-eqz v5, :cond_1

    .line 79
    .line 80
    iget-object v6, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 81
    .line 82
    invoke-virtual {v6, v5}, Landroid/widget/AdapterView;->setOnItemSelectedListener(Landroid/widget/AdapterView$OnItemSelectedListener;)V

    .line 83
    .line 84
    .line 85
    :cond_1
    iget-object v5, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 86
    .line 87
    iget-object v6, p0, Landroidx/appcompat/widget/z;->p:Landroid/view/View;

    .line 88
    .line 89
    if-eqz v6, :cond_5

    .line 90
    .line 91
    new-instance v7, Landroid/widget/LinearLayout;

    .line 92
    .line 93
    invoke-direct {v7, v0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    .line 94
    .line 95
    .line 96
    invoke-virtual {v7, v3}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 97
    .line 98
    .line 99
    new-instance v0, Landroid/widget/LinearLayout$LayoutParams;

    .line 100
    .line 101
    const/high16 v8, 0x3f800000    # 1.0f

    .line 102
    .line 103
    invoke-direct {v0, v2, v4, v8}, Landroid/widget/LinearLayout$LayoutParams;-><init>(IIF)V

    .line 104
    .line 105
    .line 106
    iget v8, p0, Landroidx/appcompat/widget/z;->q:I

    .line 107
    .line 108
    if-eqz v8, :cond_3

    .line 109
    .line 110
    if-eq v8, v3, :cond_2

    .line 111
    .line 112
    new-instance v0, Ljava/lang/StringBuilder;

    .line 113
    .line 114
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    .line 115
    .line 116
    .line 117
    const-string v5, "Invalid hint position "

    .line 118
    .line 119
    invoke-virtual {v0, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 120
    .line 121
    .line 122
    iget v5, p0, Landroidx/appcompat/widget/z;->q:I

    .line 123
    .line 124
    invoke-virtual {v0, v5}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    .line 125
    .line 126
    .line 127
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 128
    .line 129
    .line 130
    move-result-object v0

    .line 131
    const-string v5, "ListPopupWindow"

    .line 132
    .line 133
    invoke-static {v5, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    .line 134
    .line 135
    .line 136
    goto :goto_0

    .line 137
    :cond_2
    invoke-virtual {v7, v5, v0}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 138
    .line 139
    .line 140
    invoke-virtual {v7, v6}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V

    .line 141
    .line 142
    .line 143
    goto :goto_0

    .line 144
    :cond_3
    invoke-virtual {v7, v6}, Landroid/view/ViewGroup;->addView(Landroid/view/View;)V

    .line 145
    .line 146
    .line 147
    invoke-virtual {v7, v5, v0}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 148
    .line 149
    .line 150
    :goto_0
    iget v0, p0, Landroidx/appcompat/widget/z;->e:I

    .line 151
    .line 152
    if-ltz v0, :cond_4

    .line 153
    .line 154
    move v5, v1

    .line 155
    goto :goto_1

    .line 156
    :cond_4
    move v0, v4

    .line 157
    move v5, v0

    .line 158
    :goto_1
    invoke-static {v0, v5}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    .line 159
    .line 160
    .line 161
    move-result v0

    .line 162
    invoke-virtual {v6, v0, v4}, Landroid/view/View;->measure(II)V

    .line 163
    .line 164
    .line 165
    invoke-virtual {v6}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 166
    .line 167
    .line 168
    move-result-object v0

    .line 169
    check-cast v0, Landroid/widget/LinearLayout$LayoutParams;

    .line 170
    .line 171
    invoke-virtual {v6}, Landroid/view/View;->getMeasuredHeight()I

    .line 172
    .line 173
    .line 174
    move-result v5

    .line 175
    iget v6, v0, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    .line 176
    .line 177
    add-int/2addr v5, v6

    .line 178
    iget v0, v0, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    .line 179
    .line 180
    add-int/2addr v5, v0

    .line 181
    move v0, v5

    .line 182
    move-object v5, v7

    .line 183
    goto :goto_2

    .line 184
    :cond_5
    move v0, v4

    .line 185
    :goto_2
    iget-object v6, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 186
    .line 187
    invoke-virtual {v6, v5}, Landroid/widget/PopupWindow;->setContentView(Landroid/view/View;)V

    .line 188
    .line 189
    .line 190
    goto :goto_3

    .line 191
    :cond_6
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 192
    .line 193
    invoke-virtual {v0}, Landroid/widget/PopupWindow;->getContentView()Landroid/view/View;

    .line 194
    .line 195
    .line 196
    move-result-object v0

    .line 197
    check-cast v0, Landroid/view/ViewGroup;

    .line 198
    .line 199
    iget-object v0, p0, Landroidx/appcompat/widget/z;->p:Landroid/view/View;

    .line 200
    .line 201
    if-eqz v0, :cond_7

    .line 202
    .line 203
    invoke-virtual {v0}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    .line 204
    .line 205
    .line 206
    move-result-object v5

    .line 207
    check-cast v5, Landroid/widget/LinearLayout$LayoutParams;

    .line 208
    .line 209
    invoke-virtual {v0}, Landroid/view/View;->getMeasuredHeight()I

    .line 210
    .line 211
    .line 212
    move-result v0

    .line 213
    iget v6, v5, Landroid/widget/LinearLayout$LayoutParams;->topMargin:I

    .line 214
    .line 215
    add-int/2addr v0, v6

    .line 216
    iget v5, v5, Landroid/widget/LinearLayout$LayoutParams;->bottomMargin:I

    .line 217
    .line 218
    add-int/2addr v0, v5

    .line 219
    goto :goto_3

    .line 220
    :cond_7
    move v0, v4

    .line 221
    :goto_3
    iget-object v5, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 222
    .line 223
    invoke-virtual {v5}, Landroid/widget/PopupWindow;->getBackground()Landroid/graphics/drawable/Drawable;

    .line 224
    .line 225
    .line 226
    move-result-object v5

    .line 227
    if-eqz v5, :cond_8

    .line 228
    .line 229
    iget-object v6, p0, Landroidx/appcompat/widget/z;->C:Landroid/graphics/Rect;

    .line 230
    .line 231
    invoke-virtual {v5, v6}, Landroid/graphics/drawable/Drawable;->getPadding(Landroid/graphics/Rect;)Z

    .line 232
    .line 233
    .line 234
    iget-object v5, p0, Landroidx/appcompat/widget/z;->C:Landroid/graphics/Rect;

    .line 235
    .line 236
    iget v6, v5, Landroid/graphics/Rect;->top:I

    .line 237
    .line 238
    iget v5, v5, Landroid/graphics/Rect;->bottom:I

    .line 239
    .line 240
    add-int/2addr v5, v6

    .line 241
    iget-boolean v7, p0, Landroidx/appcompat/widget/z;->i:Z

    .line 242
    .line 243
    if-nez v7, :cond_9

    .line 244
    .line 245
    neg-int v6, v6

    .line 246
    iput v6, p0, Landroidx/appcompat/widget/z;->g:I

    .line 247
    .line 248
    goto :goto_4

    .line 249
    :cond_8
    iget-object v5, p0, Landroidx/appcompat/widget/z;->C:Landroid/graphics/Rect;

    .line 250
    .line 251
    invoke-virtual {v5}, Landroid/graphics/Rect;->setEmpty()V

    .line 252
    .line 253
    .line 254
    move v5, v4

    .line 255
    :cond_9
    :goto_4
    iget-object v6, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 256
    .line 257
    invoke-virtual {v6}, Landroid/widget/PopupWindow;->getInputMethodMode()I

    .line 258
    .line 259
    .line 260
    move-result v6

    .line 261
    const/4 v7, 0x2

    .line 262
    if-ne v6, v7, :cond_a

    .line 263
    .line 264
    goto :goto_5

    .line 265
    :cond_a
    move v3, v4

    .line 266
    :goto_5
    invoke-virtual {p0}, Landroidx/appcompat/widget/z;->j()Landroid/view/View;

    .line 267
    .line 268
    .line 269
    move-result-object v4

    .line 270
    iget v6, p0, Landroidx/appcompat/widget/z;->g:I

    .line 271
    .line 272
    invoke-direct {p0, v4, v6, v3}, Landroidx/appcompat/widget/z;->l(Landroid/view/View;IZ)I

    .line 273
    .line 274
    .line 275
    move-result v3

    .line 276
    iget-boolean v4, p0, Landroidx/appcompat/widget/z;->m:Z

    .line 277
    .line 278
    if-nez v4, :cond_f

    .line 279
    .line 280
    iget v4, p0, Landroidx/appcompat/widget/z;->d:I

    .line 281
    .line 282
    if-ne v4, v2, :cond_b

    .line 283
    .line 284
    goto :goto_8

    .line 285
    :cond_b
    iget v4, p0, Landroidx/appcompat/widget/z;->e:I

    .line 286
    .line 287
    const/4 v6, -0x2

    .line 288
    if-eq v4, v6, :cond_d

    .line 289
    .line 290
    const/high16 v1, 0x40000000    # 2.0f

    .line 291
    .line 292
    if-eq v4, v2, :cond_c

    .line 293
    .line 294
    invoke-static {v4, v1}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    .line 295
    .line 296
    .line 297
    move-result v1

    .line 298
    :goto_6
    move v7, v1

    .line 299
    goto :goto_7

    .line 300
    :cond_c
    iget-object v2, p0, Landroidx/appcompat/widget/z;->a:Landroid/content/Context;

    .line 301
    .line 302
    invoke-virtual {v2}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    .line 303
    .line 304
    .line 305
    move-result-object v2

    .line 306
    invoke-virtual {v2}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    .line 307
    .line 308
    .line 309
    move-result-object v2

    .line 310
    iget v2, v2, Landroid/util/DisplayMetrics;->widthPixels:I

    .line 311
    .line 312
    iget-object v4, p0, Landroidx/appcompat/widget/z;->C:Landroid/graphics/Rect;

    .line 313
    .line 314
    iget v6, v4, Landroid/graphics/Rect;->left:I

    .line 315
    .line 316
    iget v4, v4, Landroid/graphics/Rect;->right:I

    .line 317
    .line 318
    add-int/2addr v6, v4

    .line 319
    sub-int/2addr v2, v6

    .line 320
    invoke-static {v2, v1}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    .line 321
    .line 322
    .line 323
    move-result v1

    .line 324
    goto :goto_6

    .line 325
    :cond_d
    iget-object v2, p0, Landroidx/appcompat/widget/z;->a:Landroid/content/Context;

    .line 326
    .line 327
    invoke-virtual {v2}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    .line 328
    .line 329
    .line 330
    move-result-object v2

    .line 331
    invoke-virtual {v2}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    .line 332
    .line 333
    .line 334
    move-result-object v2

    .line 335
    iget v2, v2, Landroid/util/DisplayMetrics;->widthPixels:I

    .line 336
    .line 337
    iget-object v4, p0, Landroidx/appcompat/widget/z;->C:Landroid/graphics/Rect;

    .line 338
    .line 339
    iget v6, v4, Landroid/graphics/Rect;->left:I

    .line 340
    .line 341
    iget v4, v4, Landroid/graphics/Rect;->right:I

    .line 342
    .line 343
    add-int/2addr v6, v4

    .line 344
    sub-int/2addr v2, v6

    .line 345
    invoke-static {v2, v1}, Landroid/view/View$MeasureSpec;->makeMeasureSpec(II)I

    .line 346
    .line 347
    .line 348
    move-result v1

    .line 349
    goto :goto_6

    .line 350
    :goto_7
    iget-object v6, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 351
    .line 352
    sub-int v10, v3, v0

    .line 353
    .line 354
    const/4 v11, -0x1

    .line 355
    const/4 v8, 0x0

    .line 356
    const/4 v9, -0x1

    .line 357
    invoke-virtual/range {v6 .. v11}, Landroidx/appcompat/widget/v;->d(IIIII)I

    .line 358
    .line 359
    .line 360
    move-result v1

    .line 361
    if-lez v1, :cond_e

    .line 362
    .line 363
    iget-object v2, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 364
    .line 365
    invoke-virtual {v2}, Landroid/view/View;->getPaddingTop()I

    .line 366
    .line 367
    .line 368
    move-result v2

    .line 369
    iget-object v3, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 370
    .line 371
    invoke-virtual {v3}, Landroid/view/View;->getPaddingBottom()I

    .line 372
    .line 373
    .line 374
    move-result v3

    .line 375
    add-int/2addr v2, v3

    .line 376
    add-int/2addr v5, v2

    .line 377
    add-int/2addr v0, v5

    .line 378
    :cond_e
    add-int/2addr v1, v0

    .line 379
    return v1

    .line 380
    :cond_f
    :goto_8
    add-int/2addr v3, v5

    .line 381
    return v3
.end method

.method private l(Landroid/view/View;IZ)I
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 2
    .line 3
    invoke-static {v0, p1, p2, p3}, Landroidx/appcompat/widget/z$c;->a(Landroid/widget/PopupWindow;Landroid/view/View;IZ)I

    .line 4
    .line 5
    .line 6
    move-result p1

    .line 7
    return p1
.end method

.method private p()V
    .locals 2

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->p:Landroid/view/View;

    .line 2
    .line 3
    if-eqz v0, :cond_0

    .line 4
    .line 5
    invoke-virtual {v0}, Landroid/view/View;->getParent()Landroid/view/ViewParent;

    .line 6
    .line 7
    .line 8
    move-result-object v0

    .line 9
    instance-of v1, v0, Landroid/view/ViewGroup;

    .line 10
    .line 11
    if-eqz v1, :cond_0

    .line 12
    .line 13
    check-cast v0, Landroid/view/ViewGroup;

    .line 14
    .line 15
    iget-object v1, p0, Landroidx/appcompat/widget/z;->p:Landroid/view/View;

    .line 16
    .line 17
    invoke-virtual {v0, v1}, Landroid/view/ViewGroup;->removeView(Landroid/view/View;)V

    .line 18
    .line 19
    .line 20
    :cond_0
    return-void
.end method


# virtual methods
.method public A(Landroid/widget/AdapterView$OnItemClickListener;)V
    .locals 0

    .line 1
    iput-object p1, p0, Landroidx/appcompat/widget/z;->u:Landroid/widget/AdapterView$OnItemClickListener;

    .line 2
    .line 3
    return-void
.end method

.method public B(Z)V
    .locals 1

    .line 1
    const/4 v0, 0x1

    .line 2
    iput-boolean v0, p0, Landroidx/appcompat/widget/z;->k:Z

    .line 3
    .line 4
    iput-boolean p1, p0, Landroidx/appcompat/widget/z;->j:Z

    .line 5
    .line 6
    return-void
.end method

.method public D(I)V
    .locals 0

    .line 1
    iput p1, p0, Landroidx/appcompat/widget/z;->g:I

    .line 2
    .line 3
    const/4 p1, 0x1

    .line 4
    iput-boolean p1, p0, Landroidx/appcompat/widget/z;->i:Z

    .line 5
    .line 6
    return-void
.end method

.method public E(I)V
    .locals 0

    .line 1
    iput p1, p0, Landroidx/appcompat/widget/z;->e:I

    .line 2
    .line 3
    return-void
.end method

.method public b()Z
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroid/widget/PopupWindow;->isShowing()Z

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    return v0
.end method

.method public c()Landroid/widget/ListView;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 2
    .line 3
    return-object v0
.end method

.method public e()V
    .locals 13

    .line 1
    invoke-direct {p0}, Landroidx/appcompat/widget/z;->f()I

    .line 2
    .line 3
    .line 4
    move-result v0

    .line 5
    invoke-virtual {p0}, Landroidx/appcompat/widget/z;->n()Z

    .line 6
    .line 7
    .line 8
    move-result v1

    .line 9
    iget-object v2, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 10
    .line 11
    iget v3, p0, Landroidx/appcompat/widget/z;->h:I

    .line 12
    .line 13
    invoke-static {v2, v3}, Landroidx/core/widget/e;->b(Landroid/widget/PopupWindow;I)V

    .line 14
    .line 15
    .line 16
    iget-object v2, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 17
    .line 18
    invoke-virtual {v2}, Landroid/widget/PopupWindow;->isShowing()Z

    .line 19
    .line 20
    .line 21
    move-result v2

    .line 22
    const/4 v3, 0x1

    .line 23
    const/4 v4, -0x2

    .line 24
    const/4 v5, 0x0

    .line 25
    const/4 v6, -0x1

    .line 26
    if-eqz v2, :cond_c

    .line 27
    .line 28
    invoke-virtual {p0}, Landroidx/appcompat/widget/z;->j()Landroid/view/View;

    .line 29
    .line 30
    .line 31
    move-result-object v2

    .line 32
    invoke-virtual {v2}, Landroid/view/View;->isAttachedToWindow()Z

    .line 33
    .line 34
    .line 35
    move-result v2

    .line 36
    if-nez v2, :cond_0

    .line 37
    .line 38
    goto/16 :goto_c

    .line 39
    .line 40
    :cond_0
    iget v2, p0, Landroidx/appcompat/widget/z;->e:I

    .line 41
    .line 42
    if-ne v2, v6, :cond_1

    .line 43
    .line 44
    move v2, v6

    .line 45
    goto :goto_0

    .line 46
    :cond_1
    if-ne v2, v4, :cond_2

    .line 47
    .line 48
    invoke-virtual {p0}, Landroidx/appcompat/widget/z;->j()Landroid/view/View;

    .line 49
    .line 50
    .line 51
    move-result-object v2

    .line 52
    invoke-virtual {v2}, Landroid/view/View;->getWidth()I

    .line 53
    .line 54
    .line 55
    move-result v2

    .line 56
    :cond_2
    :goto_0
    iget v7, p0, Landroidx/appcompat/widget/z;->d:I

    .line 57
    .line 58
    if-ne v7, v6, :cond_7

    .line 59
    .line 60
    if-eqz v1, :cond_3

    .line 61
    .line 62
    goto :goto_1

    .line 63
    :cond_3
    move v0, v6

    .line 64
    :goto_1
    if-eqz v1, :cond_5

    .line 65
    .line 66
    iget-object v1, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 67
    .line 68
    iget v4, p0, Landroidx/appcompat/widget/z;->e:I

    .line 69
    .line 70
    if-ne v4, v6, :cond_4

    .line 71
    .line 72
    move v4, v6

    .line 73
    goto :goto_2

    .line 74
    :cond_4
    move v4, v5

    .line 75
    :goto_2
    invoke-virtual {v1, v4}, Landroid/widget/PopupWindow;->setWidth(I)V

    .line 76
    .line 77
    .line 78
    iget-object v1, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 79
    .line 80
    invoke-virtual {v1, v5}, Landroid/widget/PopupWindow;->setHeight(I)V

    .line 81
    .line 82
    .line 83
    goto :goto_4

    .line 84
    :cond_5
    iget-object v1, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 85
    .line 86
    iget v4, p0, Landroidx/appcompat/widget/z;->e:I

    .line 87
    .line 88
    if-ne v4, v6, :cond_6

    .line 89
    .line 90
    move v4, v6

    .line 91
    goto :goto_3

    .line 92
    :cond_6
    move v4, v5

    .line 93
    :goto_3
    invoke-virtual {v1, v4}, Landroid/widget/PopupWindow;->setWidth(I)V

    .line 94
    .line 95
    .line 96
    iget-object v1, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 97
    .line 98
    invoke-virtual {v1, v6}, Landroid/widget/PopupWindow;->setHeight(I)V

    .line 99
    .line 100
    .line 101
    goto :goto_4

    .line 102
    :cond_7
    if-ne v7, v4, :cond_8

    .line 103
    .line 104
    goto :goto_4

    .line 105
    :cond_8
    move v0, v7

    .line 106
    :goto_4
    iget-object v1, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 107
    .line 108
    iget-boolean v4, p0, Landroidx/appcompat/widget/z;->n:Z

    .line 109
    .line 110
    if-nez v4, :cond_9

    .line 111
    .line 112
    iget-boolean v4, p0, Landroidx/appcompat/widget/z;->m:Z

    .line 113
    .line 114
    if-nez v4, :cond_9

    .line 115
    .line 116
    goto :goto_5

    .line 117
    :cond_9
    move v3, v5

    .line 118
    :goto_5
    invoke-virtual {v1, v3}, Landroid/widget/PopupWindow;->setOutsideTouchable(Z)V

    .line 119
    .line 120
    .line 121
    iget-object v7, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 122
    .line 123
    invoke-virtual {p0}, Landroidx/appcompat/widget/z;->j()Landroid/view/View;

    .line 124
    .line 125
    .line 126
    move-result-object v8

    .line 127
    iget v9, p0, Landroidx/appcompat/widget/z;->f:I

    .line 128
    .line 129
    iget v10, p0, Landroidx/appcompat/widget/z;->g:I

    .line 130
    .line 131
    if-gez v2, :cond_a

    .line 132
    .line 133
    move v11, v6

    .line 134
    goto :goto_6

    .line 135
    :cond_a
    move v11, v2

    .line 136
    :goto_6
    if-gez v0, :cond_b

    .line 137
    .line 138
    move v12, v6

    .line 139
    goto :goto_7

    .line 140
    :cond_b
    move v12, v0

    .line 141
    :goto_7
    invoke-virtual/range {v7 .. v12}, Landroid/widget/PopupWindow;->update(Landroid/view/View;IIII)V

    .line 142
    .line 143
    .line 144
    return-void

    .line 145
    :cond_c
    iget v1, p0, Landroidx/appcompat/widget/z;->e:I

    .line 146
    .line 147
    if-ne v1, v6, :cond_d

    .line 148
    .line 149
    move v1, v6

    .line 150
    goto :goto_8

    .line 151
    :cond_d
    if-ne v1, v4, :cond_e

    .line 152
    .line 153
    invoke-virtual {p0}, Landroidx/appcompat/widget/z;->j()Landroid/view/View;

    .line 154
    .line 155
    .line 156
    move-result-object v1

    .line 157
    invoke-virtual {v1}, Landroid/view/View;->getWidth()I

    .line 158
    .line 159
    .line 160
    move-result v1

    .line 161
    :cond_e
    :goto_8
    iget v2, p0, Landroidx/appcompat/widget/z;->d:I

    .line 162
    .line 163
    if-ne v2, v6, :cond_f

    .line 164
    .line 165
    move v0, v6

    .line 166
    goto :goto_9

    .line 167
    :cond_f
    if-ne v2, v4, :cond_10

    .line 168
    .line 169
    goto :goto_9

    .line 170
    :cond_10
    move v0, v2

    .line 171
    :goto_9
    iget-object v2, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 172
    .line 173
    invoke-virtual {v2, v1}, Landroid/widget/PopupWindow;->setWidth(I)V

    .line 174
    .line 175
    .line 176
    iget-object v1, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 177
    .line 178
    invoke-virtual {v1, v0}, Landroid/widget/PopupWindow;->setHeight(I)V

    .line 179
    .line 180
    .line 181
    invoke-direct {p0, v3}, Landroidx/appcompat/widget/z;->C(Z)V

    .line 182
    .line 183
    .line 184
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 185
    .line 186
    iget-boolean v1, p0, Landroidx/appcompat/widget/z;->n:Z

    .line 187
    .line 188
    if-nez v1, :cond_11

    .line 189
    .line 190
    iget-boolean v1, p0, Landroidx/appcompat/widget/z;->m:Z

    .line 191
    .line 192
    if-nez v1, :cond_11

    .line 193
    .line 194
    goto :goto_a

    .line 195
    :cond_11
    move v3, v5

    .line 196
    :goto_a
    invoke-virtual {v0, v3}, Landroid/widget/PopupWindow;->setOutsideTouchable(Z)V

    .line 197
    .line 198
    .line 199
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 200
    .line 201
    iget-object v1, p0, Landroidx/appcompat/widget/z;->x:Landroidx/appcompat/widget/z$h;

    .line 202
    .line 203
    invoke-virtual {v0, v1}, Landroid/widget/PopupWindow;->setTouchInterceptor(Landroid/view/View$OnTouchListener;)V

    .line 204
    .line 205
    .line 206
    iget-boolean v0, p0, Landroidx/appcompat/widget/z;->k:Z

    .line 207
    .line 208
    if-eqz v0, :cond_12

    .line 209
    .line 210
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 211
    .line 212
    iget-boolean v1, p0, Landroidx/appcompat/widget/z;->j:Z

    .line 213
    .line 214
    invoke-static {v0, v1}, Landroidx/core/widget/e;->a(Landroid/widget/PopupWindow;Z)V

    .line 215
    .line 216
    .line 217
    :cond_12
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 218
    .line 219
    const/16 v1, 0x1c

    .line 220
    .line 221
    if-gt v0, v1, :cond_13

    .line 222
    .line 223
    sget-object v0, Landroidx/appcompat/widget/z;->H:Ljava/lang/reflect/Method;

    .line 224
    .line 225
    if-eqz v0, :cond_14

    .line 226
    .line 227
    :try_start_0
    iget-object v1, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 228
    .line 229
    iget-object v2, p0, Landroidx/appcompat/widget/z;->D:Landroid/graphics/Rect;

    .line 230
    .line 231
    filled-new-array {v2}, [Ljava/lang/Object;

    .line 232
    .line 233
    .line 234
    move-result-object v2

    .line 235
    invoke-virtual {v0, v1, v2}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 236
    .line 237
    .line 238
    goto :goto_b

    .line 239
    :catch_0
    move-exception v0

    .line 240
    const-string v1, "ListPopupWindow"

    .line 241
    .line 242
    const-string v2, "Could not invoke setEpicenterBounds on PopupWindow"

    .line 243
    .line 244
    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 245
    .line 246
    .line 247
    goto :goto_b

    .line 248
    :cond_13
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 249
    .line 250
    iget-object v1, p0, Landroidx/appcompat/widget/z;->D:Landroid/graphics/Rect;

    .line 251
    .line 252
    invoke-static {v0, v1}, Landroidx/appcompat/widget/z$d;->a(Landroid/widget/PopupWindow;Landroid/graphics/Rect;)V

    .line 253
    .line 254
    .line 255
    :cond_14
    :goto_b
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 256
    .line 257
    invoke-virtual {p0}, Landroidx/appcompat/widget/z;->j()Landroid/view/View;

    .line 258
    .line 259
    .line 260
    move-result-object v1

    .line 261
    iget v2, p0, Landroidx/appcompat/widget/z;->f:I

    .line 262
    .line 263
    iget v3, p0, Landroidx/appcompat/widget/z;->g:I

    .line 264
    .line 265
    iget v4, p0, Landroidx/appcompat/widget/z;->l:I

    .line 266
    .line 267
    invoke-static {v0, v1, v2, v3, v4}, Landroidx/core/widget/e;->c(Landroid/widget/PopupWindow;Landroid/view/View;III)V

    .line 268
    .line 269
    .line 270
    iget-object v0, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 271
    .line 272
    invoke-virtual {v0, v6}, Landroid/widget/AdapterView;->setSelection(I)V

    .line 273
    .line 274
    .line 275
    iget-boolean v0, p0, Landroidx/appcompat/widget/z;->E:Z

    .line 276
    .line 277
    if-eqz v0, :cond_15

    .line 278
    .line 279
    iget-object v0, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 280
    .line 281
    invoke-virtual {v0}, Landroidx/appcompat/widget/v;->isInTouchMode()Z

    .line 282
    .line 283
    .line 284
    move-result v0

    .line 285
    if-eqz v0, :cond_16

    .line 286
    .line 287
    :cond_15
    invoke-virtual {p0}, Landroidx/appcompat/widget/z;->g()V

    .line 288
    .line 289
    .line 290
    :cond_16
    iget-boolean v0, p0, Landroidx/appcompat/widget/z;->E:Z

    .line 291
    .line 292
    if-nez v0, :cond_17

    .line 293
    .line 294
    iget-object v0, p0, Landroidx/appcompat/widget/z;->B:Landroid/os/Handler;

    .line 295
    .line 296
    iget-object v1, p0, Landroidx/appcompat/widget/z;->z:Landroidx/appcompat/widget/z$e;

    .line 297
    .line 298
    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 299
    .line 300
    .line 301
    :cond_17
    :goto_c
    return-void
.end method

.method public g()V
    .locals 2

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 2
    .line 3
    if-eqz v0, :cond_0

    .line 4
    .line 5
    const/4 v1, 0x1

    .line 6
    invoke-virtual {v0, v1}, Landroidx/appcompat/widget/v;->setListSelectionHidden(Z)V

    .line 7
    .line 8
    .line 9
    invoke-virtual {v0}, Landroid/view/View;->requestLayout()V

    .line 10
    .line 11
    .line 12
    :cond_0
    return-void
.end method

.method abstract h(Landroid/content/Context;Z)Landroidx/appcompat/widget/v;
.end method

.method public i()V
    .locals 2

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroid/widget/PopupWindow;->dismiss()V

    .line 4
    .line 5
    .line 6
    invoke-direct {p0}, Landroidx/appcompat/widget/z;->p()V

    .line 7
    .line 8
    .line 9
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 10
    .line 11
    const/4 v1, 0x0

    .line 12
    invoke-virtual {v0, v1}, Landroid/widget/PopupWindow;->setContentView(Landroid/view/View;)V

    .line 13
    .line 14
    .line 15
    iput-object v1, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 16
    .line 17
    iget-object v0, p0, Landroidx/appcompat/widget/z;->B:Landroid/os/Handler;

    .line 18
    .line 19
    iget-object v1, p0, Landroidx/appcompat/widget/z;->w:Landroidx/appcompat/widget/z$i;

    .line 20
    .line 21
    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 22
    .line 23
    .line 24
    return-void
.end method

.method public j()Landroid/view/View;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->s:Landroid/view/View;

    .line 2
    .line 3
    return-object v0
.end method

.method public k()I
    .locals 1

    .line 1
    iget v0, p0, Landroidx/appcompat/widget/z;->f:I

    .line 2
    .line 3
    return v0
.end method

.method public m()I
    .locals 1

    .line 1
    iget-boolean v0, p0, Landroidx/appcompat/widget/z;->i:Z

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    const/4 v0, 0x0

    .line 6
    return v0

    .line 7
    :cond_0
    iget v0, p0, Landroidx/appcompat/widget/z;->g:I

    .line 8
    .line 9
    return v0
.end method

.method public n()Z
    .locals 2

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroid/widget/PopupWindow;->getInputMethodMode()I

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    const/4 v1, 0x2

    .line 8
    if-ne v0, v1, :cond_0

    .line 9
    .line 10
    const/4 v0, 0x1

    .line 11
    return v0

    .line 12
    :cond_0
    const/4 v0, 0x0

    .line 13
    return v0
.end method

.method public o()Z
    .locals 1

    .line 1
    iget-boolean v0, p0, Landroidx/appcompat/widget/z;->E:Z

    .line 2
    .line 3
    return v0
.end method

.method public q(Landroid/widget/ListAdapter;)V
    .locals 2

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->r:Landroid/database/DataSetObserver;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    new-instance v0, Landroidx/appcompat/widget/z$f;

    .line 6
    .line 7
    invoke-direct {v0, p0}, Landroidx/appcompat/widget/z$f;-><init>(Landroidx/appcompat/widget/z;)V

    .line 8
    .line 9
    .line 10
    iput-object v0, p0, Landroidx/appcompat/widget/z;->r:Landroid/database/DataSetObserver;

    .line 11
    .line 12
    goto :goto_0

    .line 13
    :cond_0
    iget-object v1, p0, Landroidx/appcompat/widget/z;->b:Landroid/widget/ListAdapter;

    .line 14
    .line 15
    if-eqz v1, :cond_1

    .line 16
    .line 17
    invoke-interface {v1, v0}, Landroid/widget/Adapter;->unregisterDataSetObserver(Landroid/database/DataSetObserver;)V

    .line 18
    .line 19
    .line 20
    :cond_1
    :goto_0
    iput-object p1, p0, Landroidx/appcompat/widget/z;->b:Landroid/widget/ListAdapter;

    .line 21
    .line 22
    if-eqz p1, :cond_2

    .line 23
    .line 24
    iget-object v0, p0, Landroidx/appcompat/widget/z;->r:Landroid/database/DataSetObserver;

    .line 25
    .line 26
    invoke-interface {p1, v0}, Landroid/widget/Adapter;->registerDataSetObserver(Landroid/database/DataSetObserver;)V

    .line 27
    .line 28
    .line 29
    :cond_2
    iget-object p1, p0, Landroidx/appcompat/widget/z;->c:Landroidx/appcompat/widget/v;

    .line 30
    .line 31
    if-eqz p1, :cond_3

    .line 32
    .line 33
    iget-object v0, p0, Landroidx/appcompat/widget/z;->b:Landroid/widget/ListAdapter;

    .line 34
    .line 35
    invoke-virtual {p1, v0}, Landroid/widget/AbsListView;->setAdapter(Landroid/widget/ListAdapter;)V

    .line 36
    .line 37
    .line 38
    :cond_3
    return-void
.end method

.method public r(Landroid/view/View;)V
    .locals 0

    .line 1
    iput-object p1, p0, Landroidx/appcompat/widget/z;->s:Landroid/view/View;

    .line 2
    .line 3
    return-void
.end method

.method public s(I)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Landroid/widget/PopupWindow;->setAnimationStyle(I)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method public t(I)V
    .locals 2

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 2
    .line 3
    invoke-virtual {v0}, Landroid/widget/PopupWindow;->getBackground()Landroid/graphics/drawable/Drawable;

    .line 4
    .line 5
    .line 6
    move-result-object v0

    .line 7
    if-eqz v0, :cond_0

    .line 8
    .line 9
    iget-object v1, p0, Landroidx/appcompat/widget/z;->C:Landroid/graphics/Rect;

    .line 10
    .line 11
    invoke-virtual {v0, v1}, Landroid/graphics/drawable/Drawable;->getPadding(Landroid/graphics/Rect;)Z

    .line 12
    .line 13
    .line 14
    iget-object v0, p0, Landroidx/appcompat/widget/z;->C:Landroid/graphics/Rect;

    .line 15
    .line 16
    iget v1, v0, Landroid/graphics/Rect;->left:I

    .line 17
    .line 18
    iget v0, v0, Landroid/graphics/Rect;->right:I

    .line 19
    .line 20
    add-int/2addr v1, v0

    .line 21
    add-int/2addr v1, p1

    .line 22
    iput v1, p0, Landroidx/appcompat/widget/z;->e:I

    .line 23
    .line 24
    return-void

    .line 25
    :cond_0
    invoke-virtual {p0, p1}, Landroidx/appcompat/widget/z;->E(I)V

    .line 26
    .line 27
    .line 28
    return-void
.end method

.method public u(I)V
    .locals 0

    .line 1
    iput p1, p0, Landroidx/appcompat/widget/z;->l:I

    .line 2
    .line 3
    return-void
.end method

.method public v(Landroid/graphics/Rect;)V
    .locals 1

    .line 1
    if-eqz p1, :cond_0

    .line 2
    .line 3
    new-instance v0, Landroid/graphics/Rect;

    .line 4
    .line 5
    invoke-direct {v0, p1}, Landroid/graphics/Rect;-><init>(Landroid/graphics/Rect;)V

    .line 6
    .line 7
    .line 8
    goto :goto_0

    .line 9
    :cond_0
    const/4 v0, 0x0

    .line 10
    :goto_0
    iput-object v0, p0, Landroidx/appcompat/widget/z;->D:Landroid/graphics/Rect;

    .line 11
    .line 12
    return-void
.end method

.method public w(I)V
    .locals 0

    .line 1
    iput p1, p0, Landroidx/appcompat/widget/z;->f:I

    .line 2
    .line 3
    return-void
.end method

.method public x(I)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Landroid/widget/PopupWindow;->setInputMethodMode(I)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method public y(Z)V
    .locals 1

    .line 1
    iput-boolean p1, p0, Landroidx/appcompat/widget/z;->E:Z

    .line 2
    .line 3
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 4
    .line 5
    invoke-virtual {v0, p1}, Landroid/widget/PopupWindow;->setFocusable(Z)V

    .line 6
    .line 7
    .line 8
    return-void
.end method

.method public z(Landroid/widget/PopupWindow$OnDismissListener;)V
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/appcompat/widget/z;->F:Landroid/widget/PopupWindow;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, Landroid/widget/PopupWindow;->setOnDismissListener(Landroid/widget/PopupWindow$OnDismissListener;)V

    .line 4
    .line 5
    .line 6
    return-void
.end method
