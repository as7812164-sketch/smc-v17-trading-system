.class Ln/c$a$j;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Ln/c$a;->s(Landroid/os/Bundle;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic a:Landroid/os/Bundle;

.field final synthetic b:Ln/c$a;


# direct methods
.method constructor <init>(Ln/c$a;Landroid/os/Bundle;)V
    .locals 0

    .line 1
    iput-object p1, p0, Ln/c$a$j;->b:Ln/c$a;

    .line 2
    .line 3
    iput-object p2, p0, Ln/c$a$j;->a:Landroid/os/Bundle;

    .line 4
    .line 5
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 6
    .line 7
    .line 8
    return-void
.end method


# virtual methods
.method public run()V
    .locals 2

    .line 1
    iget-object v0, p0, Ln/c$a$j;->b:Ln/c$a;

    .line 2
    .line 3
    iget-object v0, v0, Ln/c$a;->f:Ln/b;

    .line 4
    .line 5
    iget-object v1, p0, Ln/c$a$j;->a:Landroid/os/Bundle;

    .line 6
    .line 7
    invoke-virtual {v0, v1}, Ln/b;->f(Landroid/os/Bundle;)V

    .line 8
    .line 9
    .line 10
    return-void
.end method
