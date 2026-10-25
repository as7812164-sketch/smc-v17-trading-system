.class Landroidx/core/view/B$j;
.super Landroidx/core/view/B$i;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Landroidx/core/view/B;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0xa
    name = "j"
.end annotation


# instance fields
.field private n:Landroidx/core/graphics/f;

.field private o:Landroidx/core/graphics/f;

.field private p:Landroidx/core/graphics/f;


# direct methods
.method constructor <init>(Landroidx/core/view/B;Landroid/view/WindowInsets;)V
    .locals 0

    .line 1
    invoke-direct {p0, p1, p2}, Landroidx/core/view/B$i;-><init>(Landroidx/core/view/B;Landroid/view/WindowInsets;)V

    const/4 p1, 0x0

    .line 2
    iput-object p1, p0, Landroidx/core/view/B$j;->n:Landroidx/core/graphics/f;

    .line 3
    iput-object p1, p0, Landroidx/core/view/B$j;->o:Landroidx/core/graphics/f;

    .line 4
    iput-object p1, p0, Landroidx/core/view/B$j;->p:Landroidx/core/graphics/f;

    return-void
.end method

.method constructor <init>(Landroidx/core/view/B;Landroidx/core/view/B$j;)V
    .locals 0

    .line 5
    invoke-direct {p0, p1, p2}, Landroidx/core/view/B$i;-><init>(Landroidx/core/view/B;Landroidx/core/view/B$i;)V

    const/4 p1, 0x0

    .line 6
    iput-object p1, p0, Landroidx/core/view/B$j;->n:Landroidx/core/graphics/f;

    .line 7
    iput-object p1, p0, Landroidx/core/view/B$j;->o:Landroidx/core/graphics/f;

    .line 8
    iput-object p1, p0, Landroidx/core/view/B$j;->p:Landroidx/core/graphics/f;

    return-void
.end method


# virtual methods
.method h()Landroidx/core/graphics/f;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/core/view/B$j;->o:Landroidx/core/graphics/f;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    iget-object v0, p0, Landroidx/core/view/B$g;->c:Landroid/view/WindowInsets;

    .line 6
    .line 7
    invoke-static {v0}, Landroidx/core/view/O;->a(Landroid/view/WindowInsets;)Landroid/graphics/Insets;

    .line 8
    .line 9
    .line 10
    move-result-object v0

    .line 11
    invoke-static {v0}, Landroidx/core/graphics/f;->d(Landroid/graphics/Insets;)Landroidx/core/graphics/f;

    .line 12
    .line 13
    .line 14
    move-result-object v0

    .line 15
    iput-object v0, p0, Landroidx/core/view/B$j;->o:Landroidx/core/graphics/f;

    .line 16
    .line 17
    :cond_0
    iget-object v0, p0, Landroidx/core/view/B$j;->o:Landroidx/core/graphics/f;

    .line 18
    .line 19
    return-object v0
.end method

.method j()Landroidx/core/graphics/f;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/core/view/B$j;->n:Landroidx/core/graphics/f;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    iget-object v0, p0, Landroidx/core/view/B$g;->c:Landroid/view/WindowInsets;

    .line 6
    .line 7
    invoke-static {v0}, Landroidx/core/view/P;->a(Landroid/view/WindowInsets;)Landroid/graphics/Insets;

    .line 8
    .line 9
    .line 10
    move-result-object v0

    .line 11
    invoke-static {v0}, Landroidx/core/graphics/f;->d(Landroid/graphics/Insets;)Landroidx/core/graphics/f;

    .line 12
    .line 13
    .line 14
    move-result-object v0

    .line 15
    iput-object v0, p0, Landroidx/core/view/B$j;->n:Landroidx/core/graphics/f;

    .line 16
    .line 17
    :cond_0
    iget-object v0, p0, Landroidx/core/view/B$j;->n:Landroidx/core/graphics/f;

    .line 18
    .line 19
    return-object v0
.end method

.method l()Landroidx/core/graphics/f;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/core/view/B$j;->p:Landroidx/core/graphics/f;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    iget-object v0, p0, Landroidx/core/view/B$g;->c:Landroid/view/WindowInsets;

    .line 6
    .line 7
    invoke-static {v0}, Landroidx/core/view/M;->a(Landroid/view/WindowInsets;)Landroid/graphics/Insets;

    .line 8
    .line 9
    .line 10
    move-result-object v0

    .line 11
    invoke-static {v0}, Landroidx/core/graphics/f;->d(Landroid/graphics/Insets;)Landroidx/core/graphics/f;

    .line 12
    .line 13
    .line 14
    move-result-object v0

    .line 15
    iput-object v0, p0, Landroidx/core/view/B$j;->p:Landroidx/core/graphics/f;

    .line 16
    .line 17
    :cond_0
    iget-object v0, p0, Landroidx/core/view/B$j;->p:Landroidx/core/graphics/f;

    .line 18
    .line 19
    return-object v0
.end method

.method m(IIII)Landroidx/core/view/B;
    .locals 1

    .line 1
    iget-object v0, p0, Landroidx/core/view/B$g;->c:Landroid/view/WindowInsets;

    .line 2
    .line 3
    invoke-static {v0, p1, p2, p3, p4}, Landroidx/core/view/N;->a(Landroid/view/WindowInsets;IIII)Landroid/view/WindowInsets;

    .line 4
    .line 5
    .line 6
    move-result-object p1

    .line 7
    invoke-static {p1}, Landroidx/core/view/B;->s(Landroid/view/WindowInsets;)Landroidx/core/view/B;

    .line 8
    .line 9
    .line 10
    move-result-object p1

    .line 11
    return-object p1
.end method

.method public s(Landroidx/core/graphics/f;)V
    .locals 0

    .line 1
    return-void
.end method
