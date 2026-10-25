.class Lv/f$b;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Lx/a;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lv/f;->d(Landroid/content/Context;Lv/e;ILjava/util/concurrent/Executor;Lv/a;)Landroid/graphics/Typeface;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic a:Lv/a;


# direct methods
.method constructor <init>(Lv/a;)V
    .locals 0

    .line 1
    iput-object p1, p0, Lv/f$b;->a:Lv/a;

    .line 2
    .line 3
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 4
    .line 5
    .line 6
    return-void
.end method


# virtual methods
.method public bridge synthetic a(Ljava/lang/Object;)V
    .locals 0

    .line 1
    check-cast p1, Lv/f$e;

    .line 2
    .line 3
    invoke-virtual {p0, p1}, Lv/f$b;->b(Lv/f$e;)V

    .line 4
    .line 5
    .line 6
    return-void
.end method

.method public b(Lv/f$e;)V
    .locals 1

    .line 1
    if-nez p1, :cond_0

    .line 2
    .line 3
    new-instance p1, Lv/f$e;

    .line 4
    .line 5
    const/4 v0, -0x3

    .line 6
    invoke-direct {p1, v0}, Lv/f$e;-><init>(I)V

    .line 7
    .line 8
    .line 9
    :cond_0
    iget-object v0, p0, Lv/f$b;->a:Lv/a;

    .line 10
    .line 11
    invoke-virtual {v0, p1}, Lv/a;->b(Lv/f$e;)V

    .line 12
    .line 13
    .line 14
    return-void
.end method
