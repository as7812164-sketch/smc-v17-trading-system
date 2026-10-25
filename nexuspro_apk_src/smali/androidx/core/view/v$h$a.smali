.class Landroidx/core/view/v$h$a;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Landroid/view/View$OnApplyWindowInsetsListener;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Landroidx/core/view/v$h;->u(Landroid/view/View;Landroidx/core/view/q;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field a:Landroidx/core/view/B;

.field final synthetic b:Landroid/view/View;


# direct methods
.method constructor <init>(Landroid/view/View;Landroidx/core/view/q;)V
    .locals 0
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 1
    iput-object p1, p0, Landroidx/core/view/v$h$a;->b:Landroid/view/View;

    .line 2
    .line 3
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 4
    .line 5
    .line 6
    const/4 p1, 0x0

    .line 7
    iput-object p1, p0, Landroidx/core/view/v$h$a;->a:Landroidx/core/view/B;

    .line 8
    .line 9
    return-void
.end method


# virtual methods
.method public onApplyWindowInsets(Landroid/view/View;Landroid/view/WindowInsets;)Landroid/view/WindowInsets;
    .locals 3

    .line 1
    invoke-static {p2, p1}, Landroidx/core/view/B;->t(Landroid/view/WindowInsets;Landroid/view/View;)Landroidx/core/view/B;

    .line 2
    .line 3
    .line 4
    move-result-object p1

    .line 5
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 6
    .line 7
    const/16 v1, 0x1e

    .line 8
    .line 9
    const/4 v2, 0x0

    .line 10
    if-ge v0, v1, :cond_0

    .line 11
    .line 12
    iget-object v0, p0, Landroidx/core/view/v$h$a;->b:Landroid/view/View;

    .line 13
    .line 14
    invoke-static {p2, v0}, Landroidx/core/view/v$h;->a(Landroid/view/WindowInsets;Landroid/view/View;)V

    .line 15
    .line 16
    .line 17
    iget-object p2, p0, Landroidx/core/view/v$h$a;->a:Landroidx/core/view/B;

    .line 18
    .line 19
    invoke-virtual {p1, p2}, Landroidx/core/view/B;->equals(Ljava/lang/Object;)Z

    .line 20
    .line 21
    .line 22
    move-result p2

    .line 23
    if-eqz p2, :cond_0

    .line 24
    .line 25
    throw v2

    .line 26
    :cond_0
    iput-object p1, p0, Landroidx/core/view/v$h$a;->a:Landroidx/core/view/B;

    .line 27
    .line 28
    throw v2
.end method
